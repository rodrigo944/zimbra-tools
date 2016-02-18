#!/bin/bash
if ! $(python -c "import pythonzimbra" &> /dev/null); then
  command -v pip >/dev/null 2>&1 || { echo >&2 "Requires pip. Aborting..."; exit 1; }
  pip install python-zimbra
fi

if ! $(python -c "import argparse" &> /dev/null); then
  command -v pip >/dev/null 2>&1 || { echo >&2 "Requires pip. Aborting..."; exit 1; }
  pip install argparse
fi

command -v curl >/dev/null 2>&1 || { echo >&2 "Requires curl. Aborting..."; exit 1; }

curl --silent -L https://raw.githubusercontent.com/inova-tecnologias/zimbra-tools/master/utils/zdelegated.py -o /usr/local/bin/zdelegated
curl --silent -L https://github.com/inova-tecnologias/zimbra-tools/blob/master/utils/zrequests.py -o /usr/local/bin/zrequests.py

chmod 755 /usr/local/bin/zdelegated
echo "Installation completed!"
