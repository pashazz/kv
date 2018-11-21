FROM ubuntu:16.04
RUN apt-get update && apt-get install -y locales
RUN locale-gen ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LANGUAGE en_US:en  
ENV LC_ALL ru_RU.UTF-8
ADD . /vk_parser
WORKDIR /vk_parser
RUN apt-get update && apt-get install -y python3.5-dev python3.5 python3-setuptools libssl-dev libffi-dev wget build-essential xz-utils bzip2 tar
RUN  easy_install3 pip==9.0.1 && pip3 install --upgrade setuptools && pip3 install -r requirements.txt
