FROM ubuntu:24.04

##########################
# INSTALL OS DEPENDENCIES
##########################
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y \
    apt-utils \
    autoconf \
    bison \
    flex \
    gcc \
    libc6-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    libncurses5 \
    libncurses5-dev \
    libpcre3-dev \
    libreadline8 \
    libreadline-dev \
    make \
    pkg-config \
    subversion \
    git \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    cython3 \
    wget \
    tar \
    gzip \
    less \
    openssh-client \
    mg

#####################
# INSTALL LATEST CWB
#####################
# RUN svn co http://svn.code.sf.net/p/cwb/code/cwb/trunk /cwb
# WORKDIR /cwb
# RUN  sed -i 's/SITE=beta-install/SITE=standard/' config.mk && \
#     ./install-scripts/install-linux && \
#     ldconfig
RUN wget https://kumisystems.dl.sourceforge.net/project/cwb/cwb/cwb-3.5/deb/cwb_3.5.0-1_amd64.deb
RUN wget https://master.dl.sourceforge.net/project/cwb/cwb/cwb-3.5/deb/cwb-dev_3.5.0-1_amd64.deb
RUN apt-get install ./cwb_3.5.0-1_amd64.deb
RUN apt-get install ./cwb-dev_3.5.0-1_amd64.deb


##############################
# INSTALL PYTHON DEPENDENCIES
##############################
RUN python3 -m pip install --upgrade pip

RUN git clone https://github.com/ausgerechnet/cwb-ccc.git /cwb-ccc
WORKDIR /cwb-ccc
RUN git checkout v0.12.2

###############
# BUILD & TEST
###############
RUN make clean
RUN make install
RUN make compile
RUN make build
RUN make test
