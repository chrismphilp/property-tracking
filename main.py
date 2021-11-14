from rightmove import RightmovePropertiesForSale
from zoopla import ZooplaPropertiesForSale

# Rightmove Properties
RightmovePropertiesForSale(location_identifier='REGION^93929', radius_from_location=0, )  # barnet
RightmovePropertiesForSale(location_identifier='REGION^1017', radius_from_location=1, )  # northwood
RightmovePropertiesForSale(location_identifier='REGION^1154', radius_from_location=1, )  # ruislip
RightmovePropertiesForSale(location_identifier='REGION^79781', radius_from_location=0.5, )  # harrow_on_the_hill

# Zoopla Properties
ZooplaPropertiesForSale(location_identifier='barnet-london-borough', radius_from_location=0, include_sstc=False)  # barnet
