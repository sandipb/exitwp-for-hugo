""" Wordpress export file parser """

import logging
import re
from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder

from bs4 import BeautifulSoup


class NSTrackerTreeBuilder(TreeBuilder):
    "A tree builder which tracks the namespace declarations in the XML content"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespaces = {}

    def start_ns(self, prefix, ns):
        self.namespaces[prefix] = "{" + ns + "}"


class WordpressXMLParser:
    "Parser for a Wordpress export data file"

    def __init__(self, data_path, config):
        """Creates a parser object which reads the file at data_path and processes it using the config object.

        The config object is expected to have three attributes:
        - taxonomy_filter: List of category domains to exclude
        - taxonomy_entry_filter: A dictionary mapping category domains to the specific values which are to be excluded
        - body_replace: A mapping of regex to substitutions for the body content
        """
        self.data_path = data_path
        self.config = config

    def parse(self):
        """
        Parse xml file at data_path
        """
        builder = NSTrackerTreeBuilder()
        parser = XMLParser(target=builder)
        tree = ElementTree()
        logging.info("Parsing %s", self.data_path)
        root = tree.parse(self.data_path, parser)
        self.ns = builder.namespaces
        self.ns[""] = ""

        self.channel = root.find("channel")
        return {
            "header": self.parse_header(),
            "items": self.parse_items(),
        }

    def parse_header(self):
        return {
            "title": str(self.channel.find("title").text),
            "link": str(self.channel.find("link").text),
            "description": str(self.channel.find("description").text),
        }

    def parse_items(self):
        export_items = []

        xml_items = self.channel.findall("item")
        # Every item is a blog post
        for i in xml_items:
            taxonomies = i.findall("category")
            export_taxonomies = {}

            # Entries like:
            #   <category domain="post_tag" nicename="bangalore"><![CDATA[Bangalore]]></category>
            for tax in taxonomies:
                if "domain" not in tax.attrib:
                    continue
                t_domain = str(tax.attrib["domain"])  # e.g. post_tag
                t_entry = str(tax.text)  # e.g. Bangalore

                # Run the taxonomy through the config filters

                # Check if the domain is excluded: config value 'taxonomies.filter'
                if t_domain in self.config.taxonomy_filter:
                    continue

                # Check if the specific entry in the domain is excluded
                if self.config.taxonomy_entry_filter.get(t_domain) == t_entry:
                    continue

                if t_domain not in export_taxonomies:
                    export_taxonomies[t_domain] = []
                export_taxonomies[t_domain].append(t_entry)

            def gi(q, unicode_wrap=True, empty=False):
                namespace = ""
                tag = ""
                if q.find(":") > 0:
                    namespace, tag = q.split(":", 1)
                else:
                    tag = q
                try:
                    result = i.find(self.ns[namespace] + tag).text
                    # print result.encode('utf-8')
                except AttributeError:
                    result = "No Content Found"
                    if empty:
                        result = ""
                if unicode_wrap and (result is not None):
                    result = str(result)
                return result

            body = gi("content:encoded")
            for key in self.config.body_replace:
                # body = body.replace(key, body_replace[key])
                body = re.sub(key, self.config.body_replace[key], body)

            img_srcs = []
            if body is not None:
                try:
                    soup = BeautifulSoup(body, features="lxml")
                    img_tags = soup.find_all("img")
                    for img in img_tags:
                        img_srcs.append(img["src"])
                except Exception:
                    logging.exception("could not parse html: " + body)
            # print img_srcs

            excerpt = gi("excerpt:encoded", empty=True)
            post_date = gi("wp:post_date_gmt")
            if post_date == "0000-00-00 00:00:00":
                post_date = gi("wp:post_date")

            export_item = {
                "title": gi("title"),
                "link": gi("link"),
                "author": gi("dc:creator"),
                "date": post_date,
                "slug": gi("wp:post_name"),
                "status": gi("wp:status"),
                "type": gi("wp:post_type"),
                "wp_id": gi("wp:post_id"),
                "parent": gi("wp:post_parent"),
                "comments": gi("wp:comment_status") == "open",
                "taxonomies": export_taxonomies,
                "body": body,
                "excerpt": excerpt,
                "img_srcs": img_srcs,
            }
            logging.info("Extracted  %s/%s: %s (%s)", export_item["type"], export_item["wp_id"], export_item["slug"], export_item["status"])

            if export_item["type"] in self.config.item_type_filter:
                logging.info("Skipping entry as it matches exclude filter type=%s", export_item["type"])
                continue

            for field, value in self.config.item_field_filter.items():
                if export_item[field] == value:
                    logging.info("Skipping entry as it matches exclude filter %s=%s", field, value)
                    continue
            if export_item["slug"] == "None":
                import sys
                sys.exit(1)
            export_items.append(export_item)

        return export_items
