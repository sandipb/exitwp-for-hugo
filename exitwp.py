#!/usr/bin/env python
"""
exitwp - Wordpress xml exports to Jekykll blog format conversion

Tested with Wordpress 3.3.1 and jekyll 0.11.2

"""

from glob import glob
import logging
import argparse
import sys
# from urllib.parse import urlparse  # AW!!

import yaml

from internal.wpparser import WordpressXMLParser
from internal.hugowriter import HugoWriter


def read_config(path="config.yaml"):
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    # wp_exports = config["wp_exports"]
    # build_dir = config["build_dir"]
    # download_images = config["download_images"]
    # target_format = config["target_format"]
    # item_field_filter = config["item_field_filter"]
    # date_fmt = config["date_format"]
    # body_replace = config["body_replace"]
    # verbose = config["verbose"]
    config["item_type_filter"] = set(config["item_type_filter"])
    config["taxonomy_filter"] = set(config["taxonomies"]["filter"])
    config["taxonomy_entry_filter"] = config["taxonomies"]["entry_filter"]
    config["taxonomy_name_mapping"] = config["taxonomies"]["name_mapping"]
    return argparse.Namespace(**config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate wordpress to Hugo")
    parser.add_argument("-q", "--quiet", help="Reduce messages", action="store_true")
    parser.add_argument("-c", "--config", help="path to config file (default: %(default)s)", default="config.yaml")
    parser.add_argument("-d", "--data-file", help="path to the wordpress xml file")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO if not args.quiet else logging.WARNING,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    config = read_config(args.config)

    wp_exports = []
    if args.data_file is not None:
        wp_exports.append(args.data_file)
    else:
        wp_exports = glob(config.wp_exports + "/*.xml")
    if not wp_exports:
        logging.info("No input files found. Exiting.")
        sys.exit(0)

    for wpe in wp_exports:
        logging.info("Working on %s", wpe)
        data = WordpressXMLParser(wpe, config).parse()
        logging.info("Extracted %d items for '%s'", len(data["items"]), data["header"]["title"])
        # print(yaml.dump(data))
        HugoWriter(data, config).write()

    logging.info("all done")
