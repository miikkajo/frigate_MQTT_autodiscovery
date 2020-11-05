# frigate_MQTT_autodiscovery
script to generate MQTT discovery configuration for homeassistant


run autodiscovery in same directory of config.yml

script will listen for retain config messages
clean old ones and generate new configs based on config
```
#> frigate/config/
#>               config.yml
#>               
#> frigate/config$ python3 generate_configs.py
#>
```
