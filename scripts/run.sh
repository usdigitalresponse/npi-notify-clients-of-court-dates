set -x

cd ~/Documents/Github/npi-notify-clients-of-court-dates/				; if [ $? -ne 0 ] ; then exit -6 ; fi

mvn clean install
