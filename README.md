# securedrop-tooling
This git repository contains standard tooling configuration for
all the SecureDrop repositories. It will allow us to gradually
standardize on how tools are configured and developers execute
them.

Some more details on the status quo and motivation for standardization are captured in the
[Tooling, automation and developer experience](https://github.com/freedomofpress/securedrop/wiki/Tooling,-automation-and-developer-experience) wiki page.

Currently other repositories will need to be manually synchronized
with this one, in the future we may pursue some form of automation.

## Tools
The following tools are currently configured by this repository:
* [black](https://black.readthedocs.io/en/stable/)
* [isort](https://pycqa.github.io/isort/)

## License
This repository is dual-licensed under the GPL-3.0-or-later and AGPL-3.0-or-later
licenses, as the purpose is for things to be copied to SecureDrop repositories.

See the COPYING files for more details.
