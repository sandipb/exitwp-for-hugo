# ExitWP for Hugo

**UPDATE** (Sep 01 2020): This is a fork of [Arjan
Wooning](https://arjan.wooning.cz/conversion-tools-from-wordpress-to-hugo/)'s
`exit-wp` tool at https://github.com/wooni005/exitwp-for-hugo. I, (Sandip
Bhattacharya), made some large scale structural changes to the original code to
my preferred code style. It currently works with Python 3.8 and I have
successfully used it to migrate a wordpress.com website to Hugo.

Apart from the structural changes, it fixes a couple of bugs in the original
code, and adds some additional features:

- Private wordpress posts are now ported with draft set to True. An additional
  YAML header helps you distinguish these posts from real drafts.
- If images are downloaded, the original post is now modified to use this
  downloaded image. This saves a lot of time in post-migration fixes.
- You can add additional yaml headers using the config file.
- The tool now accepts the source xml path in the commandline

The rest of this README is from Arjan's original content.

---

<!-- TOC -->

- [ExitWP for Hugo](#exitwp-for-hugo)
    - [Getting started](#getting-started)
    - [Runtime dependencies](#runtime-dependencies)
        - [Installing dependencies in ubuntu/debian](#installing-dependencies-in-ubuntudebian)
        - [Installing Python dependencies using python package installer (pip)](#installing-python-dependencies-using-python-package-installer-pip)
    - [Configuration/Customization](#configurationcustomization)
    - [Known issues](#known-issues)
    - [Other Tools](#other-tools)

<!-- /TOC -->

This is a port of Thomas Frössman's ExitWP tool (for Jekyll).

You can find also a howto and background information here on my website:
https://arjan.wooning.cz/conversion-tools-from-wordpress-to-hugo/#final-solution-exitwp-for-hugo

Exitwp is tool for making migration from one or more wordpress blogs to the
[hugo blog engine](https://gohugo.io/) as easy as possible.

By default it will try to convert as much information as possible from wordpress
but can also be told to filter the amount of data it converts.

The latest version of these docs should always be available at
https://github.com/wooni005/exitwp-for-hugo

## Getting started

- [Download](https://github.com/wooni005/exitwp-for-hugo/zipball/master) or
  clone:

   ```console
   $ git clone https://github.com/wooni005/exitwp-for-hugo.git
   ...
   ```

- Export one or more wordpress blogs using the wordpress exporter under
  tools/export in wordpress admin.
- Put all wordpress xml files in the `wordpress-xml` directory
- Special note for Wordpress 3.1, you need to add a missing namespace in rss tag
  : `xmlns:atom="http://www.w3.org/2005/Atom"`
- Run xmllint on your export file and fix errors if there are.
- Run the converter by typing `./exitwp.py` in the console from the directory of
  the unzipped archive
- You should now have all the blogs converted into separate directories under
  the `build` directory

## Runtime dependencies

- [Python](http://python.org/) 3.8
- [html2text](http://www.aaronsw.com/2002/html2text/):  converts HTML to markdown (python)
- [PyYAML](http://pyyaml.org/wiki/PyYAML) : Reading configuration files and writing YAML headers (python)
- [Beautiful soup](http://www.crummy.com/software/BeautifulSoup/) : Parsing and downloading of post images/attachments (python)

### Installing dependencies in ubuntu/debian

```console
$ sudo apt-get install python-yaml python-bs4 python-html2text
...
```

### Installing Python dependencies using python package installer (pip)

From the checked out root for this project, type:

```console
$ sudo pip install --upgrade  -r pip_requirements.txt
...
```

Note that PyYAML will require other packages to compile correctly under
ubuntu/debian, these are installed by typing:

```console
$ sudo apt-get install libyaml-dev python-dev build-essential
...
```

## Configuration/Customization

See the [configuration
file](https://github.com/wooni005/exitwp-for-hugo/blob/master/config.yaml) for
all configurable options.

Some things like custom handling of non standard post types is not fully
configurable through the config file. You might have to modify the [source code
](https://github.com/wooni005/exitwp-for-hugo/blob/master/exitwp.py) to add
custom parsing behaviour.

## Known issues

- Target file names are some times less than optimal.
- ~~Rewriting of image/attachment links if they are downloaded would be a good feature~~ (**UPDATE: (sandipb) This is now supported in this fork**)
- There will probably be issues when migrating non utf-8 encoded wordpress dump
  files (if they exist).

## Other Tools

- A Gist to convert WP-Footnotes style footnotes to PHP Markdown Extra style
  footnotes: https://gist.github.com/1246047
