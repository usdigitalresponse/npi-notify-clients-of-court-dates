# NPI: Notify Clients of Court Dates

# This code is (currently) not used anywhere
Setup
- Install [Github client](https://git-scm.com/download)
- git clone https://github.com/usdigitalresponse/npi-notify-clients-of-court-dates.git
- Install [Python](https://www.python.org/downloads/), 3.10 or higher
- git clone https://github.com/neighborhood-preservation-inc/eviction-bot.git
- Follow eviction-bot setup instructions
- Environment : PYTHONPATH = C:\Users\chris\Documents\Github\eviction-bot (change path as necessary)

Recommended
- Install Visual Studio Code

While developing:
- Copy AddressScraper.py from this repository to eviction-bot repo.
- python -m pipenv run python scrapers/court/case_id.py

***
This repository falls under [U.S. Digital Response’s Code of Conduct](./CODE_OF_CONDUCT.md), and we will hold all participants in issues, pull requests, discussions, and other spaces related to this project to that Code of Conduct. Please see [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) for the full code.

## Contributing

This project wouldn’t exist without the hard work of many people. Thanks to the following for all their contributions! Please see [`CONTRIBUTING.md`](./CONTRIBUTING.md) to find out how you can help.

**Lead Maintainer:** [@chrisxkeith](https://github.com/chrisxkeith)

## License & Copyright

Copyright (C) 2022 U.S. Digital Response (USDR)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this software except in compliance with the License. You may obtain a copy of the License at:

[`LICENSE`](./LICENSE) in this repository or http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
