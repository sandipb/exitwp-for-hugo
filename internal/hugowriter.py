"Given a data structure with the content from the wordpress site, write it in Hugo format"

import re
import os
import codecs
from urllib.request import urlretrieve
from urllib.parse import urljoin, urlparse
from datetime import datetime, tzinfo, timedelta
import logging

import yaml
from html2text import html2text

HUGO_OUTPUT_SUBDIR = "hugo"

# Time definitions
ZERO = timedelta(0)
HOUR = timedelta(hours=1)


# UTC support
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


def toyaml(data, out):
    "Convert data structure to a yaml string"
    return yaml.safe_dump(data, out, allow_unicode=True, default_flow_style=False)


def html2fmt(html, target_format):
    #   html = html.replace("\n\n", '<br/><br/>')
    #   html = html.replace('<pre lang="xml">', '<pre lang="xml"><![CDATA[')
    #   html = html.replace('</pre>', ']]></pre>')
    if target_format == "html":
        return html
    else:
        return html2text(html, None)


class HugoWriter:
    def __init__(self, data, config):
        self.item_uids = {}
        self.attachments = {}
        self.data = data
        self.config = config
        self.build_dir = config.build_dir
        self.target_format = config.target_format
        self.blog_dir = os.path.normpath(os.path.join(config.build_dir, HUGO_OUTPUT_SUBDIR, self.blog_output_dirname(data)))

    def blog_output_dirname(self, item):
        """Returns the directory where the hugo blog content can be created

        If the blog link is http://blog.example.com, return blog.example.com
        """
        name = item["header"]["link"]
        name = re.sub("^https?", "", name)
        name = re.sub("[^A-Za-z0-9_.-]", "", name)
        return name

    def get_full_dir(self, dirname):
        "For a relative directory dirname, create the directory if it does not exist and return the absolute path"
        full_dir = os.path.normpath(os.path.join(self.blog_dir, dirname))
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)
        return full_dir

    def open_file(self, file):
        f = codecs.open(file, "w", encoding="utf-8")
        return f

    def get_item_uid(self, item, date_prefix=False, namespace=""):
        """Generate an unique filename for the item. If date_prefix is true, the item date is going to be used to prefix the slug"""
        result = None
        if namespace not in self.item_uids:
            self.item_uids[namespace] = {}

        if item["wp_id"] in self.item_uids[namespace]:
            result = self.item_uids[namespace][item["wp_id"]]
        else:
            uid = []
            if date_prefix:
                dt = datetime.strptime(item["date"], self.config.date_format)
                uid.append(dt.strftime("%Y-%m-%d"))
                uid.append("-")
            s_title = item["slug"]
            if s_title is None or s_title == "":
                s_title = item["title"]
            if s_title is None or s_title == "":
                s_title = "untitled"
            s_title = s_title.replace(" ", "_")
            s_title = re.sub("[^a-zA-Z0-9_-]", "", s_title)
            uid.append(s_title)
            fn = "".join(uid)
            n = 1
            # Take care of duplicates. the namespace should have an unique entry for the generated filename
            while fn in self.item_uids[namespace]:
                n = n + 1
                fn = "".join(uid) + "_" + str(n)
                self.item_uids[namespace][item["wp_id"]] = fn
            result = fn
        return result

    def generate_item_path(self, item, subdir=""):
        """Generate the full path the the target file for the item.

        For pages, a markdown file would be:
            output_dir/subdir/item["uid"]/index.markdown
        For non-pages (like posts), it would be:
            output_dir/subdir/item["uid"].markdown
        """
        full_dir = self.get_full_dir(subdir)
        filename_parts = [full_dir, "/"]
        filename_parts.append(item["uid"])
        if item["type"] == "page":
            if not os.path.exists("".join(filename_parts)):
                os.makedirs("".join(filename_parts))
            filename_parts.append("/index")
        filename_parts.append(".")
        filename_parts.append(self.target_format)
        return "".join(filename_parts)

    def generate_attachment_path(self, url, subdir, dir_prefix="images"):
        """Generate an unique local path for the url

        For url=http://example.com/a/b/d.jpg, subdir=static, dir_prefix=images
        """
        try:
            files = self.attachments[subdir]
        except KeyError:
            self.attachments[subdir] = files = {}

        try:
            filename = files[url]
        except KeyError:
            # convert http://example.com/a/b/d.jpg to /a/b/d, jpg
            file_root, file_ext = os.path.splitext(os.path.basename(urlparse(url)[2]))
            file_infix = 1
            if file_root == "":
                file_root = "1"

            # Generate an unique local filename
            current_files = list(files.values())
            maybe_filename = file_root + file_ext
            while maybe_filename in current_files:
                maybe_filename = file_root + "-" + str(file_infix) + file_ext
                file_infix = file_infix + 1
            files[url] = filename = maybe_filename

        target_dir = os.path.normpath(os.path.join(self.blog_dir, dir_prefix, subdir))
        target_file = os.path.normpath(os.path.join(target_dir, filename))
        relative_uri = os.path.normpath("/".join([self.config.blog_prefix, dir_prefix, subdir, filename]))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # if src not in attachments[dir]:
        #     print target_name
        return target_file, relative_uri

    def write(self):
        data = self.data
        for item in data["items"]:
            # if not verbose:
            #     sys.stdout.write(".")
            #     sys.stdout.flush()
            item_filename = None

            item_url = urlparse(item["link"])  # AW!!: Store item url for later url path relative
            try:
                item_date = datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC())
            except Exception:
                logging.exception("Could not parse timestamp for post: %s/%s/%s", item['wp_id'], item["type"], item["title"])
                continue

            yaml_header = {
                "title": item["title"],
                "url": item_url.path,  # AW!!: Renamed: link (Jekykll) -> url and and make url path relative
                "author": item["author"],
                "date": item_date,
                "draft": True if item["status"] == "draft" else False,
                'wordpress_id': int(item['wp_id']),  # AW!!: not used
                'comments': item['comments'],       # AW!!: Via Disqus
            }
            if item["slug"] is not None:
                yaml_header["slug"] = item['slug']
            # if len(i['excerpt']) > 0:
            #    yaml_header['excerpt'] = i['excerpt'] # AW!!: can be used

            # override yaml header values from config. Config could have a mapping like this:
            #     item_field_map:
            #       status:
            #         private:
            #           draft: True
            for field in self.config.item_field_map:
                item_val = item.get(field, "")
                if item_val in self.config.item_field_map[field]:
                    yaml_header.update(self.config.item_field_map[field][item_val])

            if item["type"] == "post":
                item["uid"] = self.get_item_uid(item, date_prefix=True)
                item_filename = self.generate_item_path(item, self.config.item_type_parent_path.get("post", "_posts"))
                yaml_header["type"] = "post"  # AW!!: Changed from layout into type
            elif item["type"] == "page":
                item["uid"] = self.get_item_uid(item)
                # Chase down parent path, if any
                parentpath = self.config.item_type_parent_path.get("page", "")
                item = item
                while item["parent"] != "0":
                    item = next((parent for parent in data["items"] if parent["wp_id"] == item["parent"]), None)
                    if item:
                        parentpath = self.get_item_uid(item) + "/" + parentpath
                    else:
                        break
                item_filename = self.generate_item_path(item, parentpath)
                yaml_header["type"] = "page"  # AW!!: Changed from layout into type
            else:
                logging.warning("Skipping unknown item type '%s' for id:%s title:%s", item["type"], item["wp_id"], item["title"])
                continue

            if item_filename is None:
                continue

            logging.info("Processing  %s/%s: %s (%s) : %s", item["type"], item["wp_id"], item["title"], item["slug"], item["status"])

            # Download images if asked for
            if self.config.download_images and len(item["img_srcs"]):
                logging.info("Downloading images for %s: %s", item["type"], item["uid"])
                for img in item["img_srcs"]:
                    try:
                        src_url = urljoin(data["header"]["link"], img)
                        local_dest, relative_uri = self.generate_attachment_path(img, item["uid"])
                        urlretrieve(src_url, local_dest)
                        logging.info(" %s -> %s", src_url, local_dest)
                        item["body"] = item["body"].replace(src_url, relative_uri)
                    except Exception:
                        logging.exception("Unable to download %s to %s", src_url, local_dest)

            # Generate the taxonomy values so that they are always at the end of the yaml header
            tax_out = {}
            for taxonomy in item["taxonomies"]:
                for tvalue in item["taxonomies"][taxonomy]:
                    t_name = self.config.taxonomy_name_mapping.get(taxonomy, taxonomy)
                    if t_name not in tax_out:
                        tax_out[t_name] = []
                    if tvalue in tax_out[t_name]:
                        continue
                    tax_out[t_name].append(tvalue)

            with codecs.open(item_filename, "w", encoding="utf-8") as out:
                try:
                    out.write("---\n")
                    if len(yaml_header) > 0:
                        toyaml(yaml_header, out)
                    if len(tax_out) > 0:
                        toyaml(tax_out, out)

                    out.write("---\n\n")
                    out.write(html2fmt(item["body"], self.target_format))
                    logging.info(" -> %s", item_filename)
                except Exception:
                    logging.exception("Parse error on: %s", item["title"])
