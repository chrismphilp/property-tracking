from rightmove import RightmovePropertiesForSale

barnet = RightmovePropertiesForSale(
    location_identifier='REGION^93929',
    max_price=465_000,
    radius_from_location=0,
)

northwood = RightmovePropertiesForSale(
    location_identifier='REGION^1017',
    max_price=465_000,
    radius_from_location=1,
)

ruislip = RightmovePropertiesForSale(
    location_identifier='REGION^1154',
    max_price=465_000,
    radius_from_location=1,
)

harrow_on_the_hill = RightmovePropertiesForSale(
    location_identifier='REGION^79781',
    max_price=465_000,
    radius_from_location=0.5,
)
