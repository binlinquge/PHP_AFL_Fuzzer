echo "Instrumenting application CE-phoenix..."
cd ./PHP-Fuzzer
python3 instrument.py ./cephoenix
cd ..
read i

echo "Getting parameters from static analysis..."
cd ./AFL/AFL/
python3 Gen_input.py
read i

echo "Start fuzzing..."
sudo ./afl-fuzz -i input -o output -m 1024 ./CE-Phoenix-master/contact_us.php

