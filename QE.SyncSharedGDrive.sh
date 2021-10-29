#! /bin/bash

#### This code updates local files from a shared google drive folder
# It uses curl and rclone running in a Ubuntu 20.04 setup
# Installed and configured from instructions in https://www.howtogeek.com/451262/how-to-use-rclone-to-back-up-to-google-drive-on-linux/
# Aditional information from https://rclone.org/commands/
# Sebastian Godoy Gutiérrez, 29/10/2021

echo '    > Actualizando carpeta local con contenidos compartidos en google drive'

/usr/bin/rclone sync --update --verbose --transfers 30 --checkers 8 --contimeout 60s --timeout 300s --retries 3 --low-level-retries 10 "google-drive:comprobacion2" "/home/seba/Perovskite_Diol/SharedFolder_GDrive"


echo '    > Completo!'
notify-send 'Descarga de GDrive (Peroskovite-diol) completa'
