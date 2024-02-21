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
