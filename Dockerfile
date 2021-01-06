# base image contains the data
#FROM python:3.8
# COPY --from=mopd/crims-data:latest /app/data /app/data
FROM mopd/crims-data:latest
# # COPY --from=openjdk:8-jdk / / # python lost

WORKDIR /app

COPY crims /app/crims
COPY requirements.txt /app
#COPY LICENSE /app
COPY netlogo_adapter.py /app
COPY event-response-with-shifts.nlogo /app
COPY netlogo-gui.sh /app

RUN apt-get update -y \
 && apt-get install -y --no-install-recommends -y tar openjdk-11-jre \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*


# # ensure pip is up to date and install deps
RUN python -m pip install -U pip \
 && python -m pip install -r requirements.txt

# # ENV NETLOGO_VERSION=6.2.0
# # ENV NETLOGO_INSTALL_DIR="NetLogo $NETLOGO_VERSION"

# RUN wget https://ccl.northwestern.edu/netlogo/${NETLOGO_VERSION}/NetLogo-${NETLOGO_VERSION}-64.tgz \
#  && tar xzf NetLogo-$NETLOGO_VERSION-64.tgz \
#  && ln -s "${NETLOGO_INSTALL_DIR}/NetLogo" \
#  && rm NetLogo-${NETLOGO_VERSION}-64.tgz
COPY NetLogo-6.2.0-64.tgz .
RUN tar xzf NetLogo-6.2.0-64.tgz \
 && ln -s "./NetLogo 6.2.0/NetLogo" \
 && rm NetLogo-6.2.0-64.tgz

CMD ["./netlogo-gui.sh", "event-response-with-shifts.nlogo"]
#CMD ["/bin/bash"]
