import React from 'react'
import { GeoapifyGeocoderAutocomplete, GeoapifyContext } from '@geoapify/react-geocoder-autocomplete'
// import '@geoapify/geocoder-autocomplete/styles/minimal.css'

interface PlacesAutoCompleteProps {
  onPlaceSelect: (lat: number, lon: number) => void
}

const PlacesAutoComplete: React.FC<PlacesAutoCompleteProps> = ({ onPlaceSelect }) => {
  const type = 'city'
  const displayValue = ''
  return (
    <GeoapifyContext apiKey={process.env.NEXT_PUBLIC_GEOAPIFY_API_KEY}>
      <GeoapifyGeocoderAutocomplete
        placeholder="Enter address here"
        type={type}
        value={displayValue}
        placeSelect={(value) => {
          if (value && value.properties) {
            const lat = value.properties.lat
            const lon = value.properties.lon
            // console.log("Selected coordinates:", lat, lon)
            onPlaceSelect(lat, lon) // send coords back to parent
          }
        }}
      />
    </GeoapifyContext>
  )
}

export default PlacesAutoComplete
