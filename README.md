# Flockr

Tool to manage LXC containers and XenServer VHD appliances on CloudStack

## Installation

### Requirements

- CloudStack
- filemagic
- pyyaml
- termcolor
- requests

First, clone it here on GitHub:

```shell
~ # git clone https://github.com/theflockers/flockr
~ # cd flockr
~flockr # python setup.py install
```
## Usage

Setup will create the **Flockr** configuration at */etc/flockr/flockr.yaml-example*, so you can rename it to flockr.yaml. They have the following content:

```shell
production:
  apikey: your_api_key
  url: cloudstack_url 
  expires: 600
  secretkey: your_secret_key
  timeout: 3600
  verifysslcert: true
```

Replace the content with your credentials, then you can create your first **LXC application container**:

```shell
~ # flockr -c myapp
=> CREATED:  application myapp
```
It will generate the following configuration file  (config.yaml) inside the myapp directory:
```shell
~ # cat myapp/config.yaml
build:
  tmpdir: /tmp
  base_format: TAR
  base_url: base_operating_system_path_or_url
  application_repository: application_repository_git_path_or_url
  application_wwwroot: /var/www/html/
  repository_type: TAR_or_GIT

template:
  zoneid: cloudstack_zone_id
  ostype: cloudstack_os_type_string_name
  upload_url: url_to_upload_to-must_have_put_option_enabled
  display_url: url_that_cloudstack_sees
  hypervisor: LXC
  format: tar
  hvm: false
  passwordenabled: true
  isextractable: true
  versionate: true

deploy:
  security_groups: security_groups_separeted_by_comma
  zoneid: cloudstack_zone_id
  instance_size: instance_size_name
```

#### Fields:
###### build:
- tmpdir: temporary directory used to build the appliance;
- base_format: only TAR available;
- base_url: url to fetch the base O.S. from - Only TAR enabled;
- application_repository: Where to get the code! 
- application_wwwroot: where to put the code!
- repository_type: TAR or GIT;

###### template:
- zoneid: cloudstack zone id;
- ostype: string containing Cloudstack O.S type (Ex. "CentOS 7");
- upload_url: Upload URL; Must have PUT method enabled;
- display_url: URL that cloudstack sees to fetch the template from;
- hypervisor: LXC or XenServer;
- format: TAR or VHD;
- hvm: Always false;
- passwordenabled: If the template has the password script enabled;
- isextractable: If template is compacted;
- versionate: unused yet;

###### deploy:
- security_groups: A comma separeted string of security groups names;
- zoneid: cloudstack zone id;
- instance_size: instance size name to use to deploy nodes;

You must replace with your own information and then you can build your first application

```shell
~ # flockr --build --application-name myapp --build-type lxc

* Building app myapp *

Base S.O. archive format: TAR

=> Cleaning up tmpdir /tmp/flockr-build
=> Extracting Base S.O. files to /tmp/flockr-build/root-fs
=> Fetching application from http://deploy.myserver.com.br/application-current.tar.gz
=> Merging /tmp/flockr-build/app/ with base s.o. into /tmp/flockr-build/root-fs//var/www/html/
=> Creating archive myapp/myapp.tar

+++ Build done. Now you may want to register a template +++
```
Once it finished, you can register your application template. Flockr will upload your template and create a new
Cloudstack template pointing to it:

```shell
~ # flockr --template --register --application-name myapp --template-version=v1.0
=> Template myapp:v1.0 created 
++ TIP: Use --list to see if is it ready ++
~ #
~ # flockr --template --list --application-name myapp
=> myapp:v1.0 Download Complete
```
Then, you can deploy your first **LXC application container**!

```shell
~ # flockr --deploy --application-name=myapp --template-version=v1.0 --num-nodes 3
=> SUCCESS: 3 nodes deployed
~ # flockr --node --list --application-name myapp
~ # flockr --node --application-name=myapp --list
=> myapp-26 (small.local) myapp:v1.0 Starting
=> myapp-70 (small.local) myapp:v1.0 Starting
=> myapp-73 (small.local) myapp:v1.0 Starting
~ # flockr --node --application-name=myapp --list
=> myapp-26 (small.local) myapp:v1.0 Starting
=> myapp-70 (small.local) myapp:v1.0 Starting
=> myapp-73 (small.local) myapp:v1.0 Running
~ # flockr --node --application-name=myapp --list
=> myapp-26 (small.local) myapp:v1.0 Starting
=> myapp-70 (small.local) myapp:v1.0 Running
=> myapp-73 (small.local) myapp:v1.0 Running
~ # flockr --node --application-name=myapp --list
=> myapp-26 (small.local) myapp:v1.0 Running
=> myapp-70 (small.local) myapp:v1.0 Running
=> myapp-73 (small.local) myapp:v1.0 Running
```
## TODO
- use a database (bdb or sqlite) to save application data;
- save the hosts indexes inside the database;
- Caught the exceptions;
- finish the VHD feature for XenServer usage;
- can't remember now!
