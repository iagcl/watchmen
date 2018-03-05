FROM centos:latest

RUN yum clean all
RUN yum -y install epel-release
RUN sed -i "s/mirrorlist=https/mirrorlist=http/" /etc/yum.repos.d/epel.repo

RUN yum -y install python-pip PyYAML python-jinja2 python-httplib2 python-keyczar python-paramiko python-setuptools git which zip

COPY docker/requirements.txt .
RUN pip install -r requirements.txt

# Install git-secret
RUN git clone https://github.com/awslabs/git-secrets.git
RUN cd git-secrets && make install

WORKDIR /data
# entry command
CMD ["/bin/bash"]
