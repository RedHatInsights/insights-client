#!/usr/bin/bash -ux

# Stolen from
# https://github.com/RedHatInsights/insights-core/blob/master/insights/tests/client/test_crypto.py
# https://gitlab.cee.redhat.com/mhorky/tasks/-/blob/main/CCT-131/steps.md#prepare-the-vm

cat >public.armor.key << EOF
-----BEGIN PGP PUBLIC KEY BLOCK-----

mDMEZpbJQRYJKwYBBAHaRw8BAQdA3HBHO0ADUcKgqaTbj6BUU82ZbJ5ojhTdju7b
9+NGtEm0GkNDVCBRRSA8Y2N0LXFlQHJlZGhhdC5jb20+iJMEExYKADsWIQQbHWyM
LBEKAqrK4N73Fp/8VshPuwUCZpbJQQIbAwULCQgHAgIiAgYVCgkICwIEFgIDAQIe
BwIXgAAKCRD3Fp/8VshPu3qhAQDWOV+kGpIGdLBRqIuQZCFAH5rS/6HW7J16CuS5
qub0ZgEAvSiIanOj1TaGHnYOyHXi0694Amfvr3Txzligo62OwwW4OARmlslBEgor
BgEEAZdVAQUBAQdAbCvp9o2XYSmtQweCmRBKcYUUPfzkoENeB+AehOxiMl0DAQgH
iHgEGBYKACAWIQQbHWyMLBEKAqrK4N73Fp/8VshPuwUCZpbJQQIbDAAKCRD3Fp/8
VshPu+vWAQCW0w/EIsPMPnlecizvNf3pXydze5XotIr4XFrJaB465AD8CVn5JDN2
5lg1O5u16Ww3WAaT01FCealgq+NnG/03IAI=
=xnEk
-----END PGP PUBLIC KEY BLOCK-----
EOF

cat >private.armor.key << EOF
-----BEGIN PGP PRIVATE KEY BLOCK-----

lFgEZpbJQRYJKwYBBAHaRw8BAQdA3HBHO0ADUcKgqaTbj6BUU82ZbJ5ojhTdju7b
9+NGtEkAAQDKnXHYfXWHpRQiNTPU8mqVcOg3M7VlZPxMgcEJH4bi2BBktBpDQ1Qg
UUUgPGNjdC1xZUByZWRoYXQuY29tPoiTBBMWCgA7FiEEGx1sjCwRCgKqyuDe9xaf
/FbIT7sFAmaWyUECGwMFCwkIBwICIgIGFQoJCAsCBBYCAwECHgcCF4AACgkQ9xaf
/FbIT7t6oQEA1jlfpBqSBnSwUaiLkGQhQB+a0v+h1uydegrkuarm9GYBAL0oiGpz
o9U2hh52Dsh14tOveAJn76908c5YoKOtjsMFnF0EZpbJQRIKKwYBBAGXVQEFAQEH
QGwr6faNl2EprUMHgpkQSnGFFD385KBDXgfgHoTsYjJdAwEIBwAA/0lTtr1yPIFe
+3xHwOEaA9K3Iss8unb7v8jAPTIUnRoYEI2IeAQYFgoAIBYhBBsdbIwsEQoCqsrg
3vcWn/xWyE+7BQJmlslBAhsMAAoJEPcWn/xWyE+769YBAJbTD8Qiw8w+eV5yLO81
/elfJ3N7lei0ivhcWsloHjrkAPwJWfkkM3bmWDU7m7XpbDdYBpPTUUJ5qWCr42cb
/TcgAg==
=YrcZ
-----END PGP PRIVATE KEY BLOCK-----
EOF

gpg --import public.armor.key
gpg --import private.armor.key
KEYID=$(gpg --list-secret-keys --keyid-format long cct-qe \
  | grep sec | awk '{ split($2, a, "/"); print a[2] }')
gpg --output public.gpg --export $KEYID

mv /etc/insights-client/redhattools.pub.gpg{,.original}
mv ./public.gpg /etc/insights-client/redhattools.pub.gpg.dev
mkdir temp && chmod 700 temp
gpg --homedir temp --import /etc/insights-client/redhattools.pub.gpg.*
gpg --homedir temp --export > /etc/insights-client/redhattools.pub.gpg
rm -rf temp/

mv /etc/insights-client/rpm.egg{,.original}
mv /etc/insights-client/rpm.egg.asc{,.original}

currDir=$PWD
cd ~/
git clone https://github.com/RedHatInsights/insights-core.git
cd insights-core
git switch $insightsCoreBranch

./build_client_egg.sh
cp insights.zip last_stable.egg
gpg --detach-sign -u $KEYID --armor last_stable.egg
cp last_stable.egg last_stable.egg.asc /var/lib/insights/

sed -ie 's/#auto_update=True/auto_update=False/g' \
  /etc/insights-client/insights-client.conf

cd $currDir
