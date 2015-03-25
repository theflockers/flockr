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

## Fields:
#### build:
- tmpdir: temporary directory used to build the appliance
- base_format: only TAR available
- base_url: url to fetch the base O.S. from - Only TAR enabled
- application_repository: Where to get the code! 
- application_wwwroot: where to put the code!
- repository_type: TAR or GIT

You must replace with your own information and then you can build your first application

