# Copyright (c) 2007-2012 Dell, Inc. by Matt Domsch <Matt_Domsch@dell.com>
# Copyright (c) 2015,2018 Adrian Reber <adrian@lisas.de>
#
# Based on examples from python-GeoIP and python-basemap-examples
# Licensed under the GNU General Public License v2
# because it uses data from python-basemap-data which is GPL
# while the rest of MirrorManager is licensed MIT/X11


import codecs
import os
import socket
from urllib.parse import urlsplit

import click
import geoip2.database
import matplotlib

import mirrormanager2.lib
from mirrormanager2.lib.database import get_db_manager

from .common import config_option

matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas  # noqa: E402
from mpl_toolkits.basemap import Basemap  # noqa: E402
from pylab import figure  # noqa: E402


def uniq(input):
    seen = set()
    seen_add = seen.add
    return [x for x in input if not (x in seen or seen_add(x))]


def lookup_host_locations(config, gi):
    db_manager = get_db_manager(config)
    session = db_manager.Session()
    hcurls = mirrormanager2.lib.get_host_category_url(session)

    results = []
    tracking = []
    embargoed_countries = set([x.upper() for x in list(config["EMBARGOED_COUNTRIES"])])

    for hcurl in hcurls:
        if hcurl.host_category.host.private or hcurl.host_category.host.site.private:
            continue
        hn = urlsplit(hcurl.url)[1]
        if hn in tracking:
            continue
        try:
            ip = socket.gethostbyname(hn)
            gir = gi.city(ip)
        except Exception:
            continue
        try:
            name = hcurl.host_category.host.site.name
        except Exception:
            name = "N/A"
        if gir is not None:
            if gir.country.iso_code in embargoed_countries:
                print("skipping " + hn)
                continue
            t = (hn, gir.country.iso_code, gir.location.latitude, gir.location.longitude)
            print("{} {} {} {}".format(*t))
            results.append([t, name])
            tracking.append(hn)

    session.close()

    return results


def doit(output, config):
    gi = geoip2.database.Reader(os.path.join(config["GEOIP_BASE"], "GeoLite2-City.mmdb"))
    m = Basemap(
        llcrnrlon=-180.0,
        llcrnrlat=-90,
        urcrnrlon=180.0,
        urcrnrlat=90.0,
        resolution="c",
        projection="cyl",
    )
    # plot them as filled circles on the map.
    # first, create a figure.
    dpi = 100
    dimx = 800 / dpi
    dimy = 400 / dpi
    fig = figure(figsize=(dimx, dimy), dpi=dpi, frameon=False, facecolor="blue")
    # take up the whole space
    fig.add_axes([0.0, 0.0, 1.0, 1.0])
    canvas = FigureCanvas(fig)
    # background color will be used for 'wet' areas.
    # use zorder=10 to make sure markers are drawn last.
    # (otherwise they are covered up when continents are filled)
    results = lookup_host_locations(config, gi)
    os.makedirs(output)
    marker_url = config.get("APPLICATION_ROOT", "/") + "static/map/f-dot.png"
    fd = codecs.open(os.path.join(output, "mirrors_location.txt"), "w", "utf-8-sig")
    fd.write("lat\tlon\ttitle\tdescription\ticonSize\ticonOffset\ticon\n")
    for t in results:
        lat = t[0][2]
        lon = t[0][3]
        # draw a red dot at the center.
        xpt, ypt = m(lon, lat)
        m.plot([xpt], [ypt], "ro", zorder=10)
        fd.write(
            f"{t[0][2]}\t{t[0][3]}\t<a href='http://{t[0][0]}/' rel='noopener noreferrer' "
            f"target='_blank'>{t[0][0]}</a>"
            f"\t{t[1]}\t21,25\t-10,-25\t{marker_url}\n"
        )

    fd.close()
    # draw coasts and fill continents.
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    m.fillcontinents(color="green")
    canvas.print_figure(output + "/map.png", dpi=100)


@click.command()
@config_option
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    required=True,
    help="write output to DIR",
)
def main(config, output):
    config = mirrormanager2.lib.read_config(config)
    doit(output, config)
