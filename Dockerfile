FROM fedora:37

WORKDIR /mirrormanager2

COPY . .

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && \
    python3 -m pip install -r requirements.txt && \
    cp /usr/local/lib/python3.11/site-packages/flask_xmlrpcre/xmlrpcre.py /usr/local/lib/python3.11/site-packages/flaskext/xmlrpc.py && \
    cp -r mirrormanager2/admin/. /usr/local/lib/python3.11/site-packages/flask_admin/static/. && \
    cd vendor/pyrpmmd &&  \
    python3 setup.py install

ENTRYPOINT ["/mirrormanager2/start.sh"]
