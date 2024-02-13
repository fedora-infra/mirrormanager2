# Copyright (C) 2015 by Adrian Reber
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import logging
import os

import matplotlib

matplotlib.use("Agg")

import click  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import rc  # noqa: E402

from mirrormanager2.lib import get_repositories, read_config  # noqa: E402
from mirrormanager2.lib.constants import PROPAGATION_ARCH  # noqa: E402
from mirrormanager2.lib.database import get_db_manager  # noqa: E402

from .common import config_option, setup_logging  # noqa: E402

logger = logging.getLogger(__name__)


font = {"size": 9}

rc("font", **font)


def list_adder(a, b):
    return [i + j for i, j in zip(a, b)]


def label_bars_size(rects, fmt, ax, offset=None, last=False):
    if offset is None:
        offset = []
    i = 0
    for rect in rects:
        int(rect.get_width())

        xloc = rect.get_x() + rect.get_width() / 2.0
        try:
            plus = offset[i]
        except Exception:
            plus = 0

        if rect.get_height() > 8:
            yloc = rect.get_height() / 2 + plus + 3
        else:
            yloc = rect.get_height() + plus - 1.2

        if rect.get_height() > 6:
            ax.text(
                xloc,
                yloc,
                fmt % rect.get_height(),
                horizontalalignment="center",
                rotation="horizontal",
                verticalalignment="top",
                color="white",
            )
        i += 1

        if last:
            ax.text(
                xloc,
                rect.get_height() + plus + 6,
                fmt % float(plus + rect.get_height()),
                horizontalalignment="center",
                rotation="horizontal",
                verticalalignment="top",
                color="black",
            )


# @click.option(
#     "--prefix",
#     default="development",
#     help="Specify a prefix which should be added to the output files",
# )
# @click.option(
#     "--outdir",
#     required=True,
#     help="Specifiy directory into which the output should be placed",
# )
# def main(logfiles, prefix, outdir, debug):
#     repomd_same = []
#     repomd_one_day = []
#     repomd_two_day = []
#     repomd_other = []
#     repomd_none = []
#     labels = []
#     maximum = 0
#     sha256sums = []

#     hosts_broken = {}
#     hosts_older = {}
#     hosts_older_1 = {}
#     hosts_older_2 = {}

#     # add the output directory to the prefix
#     prefix = os.path.join(outdir, prefix)

#     total = len(glob.glob(logfiles))

#     if not total:
#         print("No input files found at: " + logfiles)
#         sys.exit(0)

#     remaining = total
#     if debug:
#         print("%d data points available" % total)

#     proppath = None

#     for filename in sorted(glob.glob(logfiles)):
#         for line in open(filename):
#             line = line.rstrip()
#             line = line.split("::")
#             try:
#                 if not proppath:
#                     proppath = line[7]
#                 if line[5] not in sha256sums:
#                     if len(line[5]) == 64:
#                         # sha256sum is 64 character long
#                         sha256sums.append(line[5])
#             except Exception:
#                 pass

#     for filename in sorted(glob.glob(logfiles)):
#         total -= 1
#         if total > 58:
#             remaining -= 1
#             continue
#         if remaining > 30 and total % 2 == 0:
#             continue
#         remaining -= 1
#         same = 0
#         one_day = 0
#         two_day = 0
#         other = 0
#         none = 0
#         scandate = None

#         for line in open(filename):
#             line = line.rstrip()
#             line = line.split("::")
#             if len(line) <= 6:
#                 continue
#             try:
#                 date = line[4].split("-")
#                 scandate = "{}-{}-{}\n{}-{}-{}".format(*tuple(date))
#             except Exception:
#                 continue
#             if line[3] == "NOSUM":
#                 none += 1
#                 try:
#                     hosts_broken[line[1]] += 1
#                 except Exception:
#                     hosts_broken[line[1]] = 1
#             elif line[6] != "200":
#                 continue
#             elif line[3] == line[5]:
#                 same += 1
#             elif len(line[5]) != 64:
#                 other += 1
#             elif line[3] in sha256sums:
#                 offset = sha256sums.index(line[5])
#                 if sha256sums.index(line[3]) == offset:
#                     same += 1
#                 elif sha256sums.index(line[3]) == offset - 1:
#                     one_day += 1
#                     try:
#                         hosts_older_1[line[1]] += 1
#                     except Exception:
#                         hosts_older_1[line[1]] = 1
#                 elif sha256sums.index(line[3]) == offset - 2:
#                     two_day += 1
#                     try:
#                         hosts_older_2[line[1]] += 1
#                     except Exception:
#                         hosts_older_2[line[1]] = 1
#                 else:
#                     other += 1
#             else:
#                 other += 1
#                 try:
#                     hosts_older[line[1]] += 1
#                 except Exception:
#                     hosts_older[line[1]] = 1
#         if none + same + other + one_day + two_day > maximum:
#             maximum = none + same + other + one_day + two_day

#         repomd_same.append(same)
#         repomd_one_day.append(one_day)
#         repomd_two_day.append(two_day)
#         repomd_other.append(other)
#         repomd_none.append(none)
#         labels.append(scandate)

#     if debug:
#         print("%d data points used" % len(repomd_same))


def make_graph(repository, outdir):
    prefix = f"{repository.version.product.name} {repository.version.name}"
    stats = repository.propagation_stats
    labels = [ps.datetime.strftime(r"%Y-%m-%d\n%H-%M-%S") for ps in stats]
    repomd_same = [ps.same_day for ps in stats]
    repomd_one_day = [ps.one_day for ps in stats]
    repomd_two_day = [ps.two_day for ps in stats]
    repomd_older = [ps.older for ps in stats]
    repomd_no_info = [ps.no_info for ps in stats]
    proppath = repository.directory.name

    maximums = [(ps.same_day + ps.one_day + ps.two_day + ps.older + ps.no_info) for ps in stats]
    maximum = max(maximums)

    # with open(os.path.join(outdir, f"{prefix}-repomd-report.txt"), "w") as fd:
    #     logger.debug("Hosts broken")
    #     fd.write("Hosts broken\n")
    #     for url, count in sorted(hosts_broken.items(), key=lambda x: (int(x[1])), reverse=True):
    #         logger.debug(f"{url}: {count}")
    #         fd.write(f"{url}: {count}\n" % (url, count))

    #     logger.debug("Hosts older")
    #     fd.write("Hosts older\n")
    #     for url, count in sorted(hosts_older.items(), key=lambda x: (int(x[1])), reverse=True):
    #         logger.debug("%s: %d" % (url, count))
    #         fd.write("%s: %d\n" % (url, count))

    #     logger.debug("Hosts older - 1")
    #     fd.write("Hosts older - 1\n")
    #     for url, count in sorted(hosts_older_1.items(), key=lambda x: (int(x[1])), reverse=True):
    #         logger.debug("%s: %d" % (url, count))
    #         fd.write("%s: %d\n" % (url, count))
    #     fd.write("Hosts older - 2\n")

    #     logger.debug("Hosts older - 2")
    #     for url, count in sorted(hosts_older_2.items(), key=lambda x: (int(x[1])), reverse=True):
    #         logger.debug("%s: %d" % (url, count))
    #         fd.write("%s: %d\n" % (url, count))

    ind = np.arange(len(labels))
    width = 0.62

    fig = plt.figure(figsize=(14, 7))
    ax = fig.add_subplot(111)

    rects = ax.bar(ind, repomd_same, width, color="g", label="synced")
    label_bars_size(rects, "%.0f", ax)

    rects = ax.bar(
        ind, repomd_one_day, width, bottom=repomd_same, color="mediumvioletred", label="synced - 1"
    )
    label_bars_size(rects, "%.0f", ax, repomd_same)

    bottom = list_adder(repomd_same, repomd_one_day)
    rects = ax.bar(ind, repomd_two_day, width, bottom=bottom, color="b", label="synced - 2")
    label_bars_size(rects, "%.0f", ax, bottom)

    bottom = list_adder(bottom, repomd_two_day)
    rects = ax.bar(ind, repomd_older, width, bottom=bottom, color="red", label="older")
    label_bars_size(rects, "%.0f", ax, bottom)

    bottom = list_adder(bottom, repomd_older)
    rects = ax.bar(ind, repomd_no_info, width, bottom=bottom, color="y", label="N/A")
    label_bars_size(rects, "%.0f", ax, bottom, True)

    ax.set_ylim(0, maximum + 40)
    ax.set_xticks(ind + width)
    ax.set_xticklabels(labels)
    plt.setp(plt.xticks()[1], rotation=90)

    plt.legend(loc=2, shadow=True, fancybox=True, ncol=3)

    plt.title(f"repomd.xml propagation for {proppath}")

    day = labels[-1].split(r"\n")[0]
    pdfpath = os.path.join(outdir, f"{prefix:<}-{day}-repomd-propagation.pdf")
    plt.savefig(pdfpath, bbox_inches="tight")

    svgpath = os.path.join(outdir, f"{prefix}-{day}-repomd-propagation.svg")
    plt.savefig(svgpath, bbox_inches="tight")

    logger.debug(pdfpath)

    plt.savefig(os.path.join(outdir, f"{prefix}-repomd-propagation.pdf"), bbox_inches="tight")
    plt.savefig(os.path.join(outdir, f"{prefix}-repomd-propagation.svg"), bbox_inches="tight")


@click.command()
@config_option
@click.option(
    "--repo-prefix",
    "repo_prefixes",
    default=["rawhide"],
    multiple=True,
    help="Repository prefix to use for propagation. Defaults to 'rawhide'.",
)
@click.option(
    "--outdir",
    required=True,
    help="Specifiy directory into which the output should be placed",
)
@click.option("--debug", is_flag=True, default=False, help="enable debugging")
def main(config, repo_prefixes, outdir, debug):
    setup_logging(debug)
    config = read_config(config)
    db_manager = get_db_manager(config)
    with db_manager.Session() as session:
        for repository in get_repositories(
            session, prefixes=repo_prefixes, arches=[PROPAGATION_ARCH]
        ):
            make_graph(repository, outdir)
