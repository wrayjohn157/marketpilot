#!/bin/bash

echo "=== Checking 15m RSI & StochRSI values ==="

# List all keys matching *_15m_RSI14
symbols=$(redis-cli keys '*_15m_RSI14' | sed 's/_15m_RSI14//')

for symbol in $symbols; do
  rsi=$(redis-cli get "${symbol}_15m_RSI14")
  k=$(redis-cli get "${symbol}_15m_StochRSI_K")
  d=$(redis-cli get "${symbol}_15m_StochRSI_D")

  echo -e "\n🔹 ${symbol}:"
  echo "  RSI14          = $rsi"
  echo "  StochRSI_K     = $k"
  echo "  StochRSI_D     = $d"

  [[ "$rsi" != *[0-9]* ]] && echo "  ⚠️  Malformed or missing RSI!"
  [[ "$k" != *[0-9]* ]] && echo "  ⚠️  Malformed or missing StochRSI_K!"
  [[ "$d" != *[0-9]* ]] && echo "  ⚠️  Malformed or missing StochRSI_D!"
done

echo -e "\n=== Checking 1h indicator JSON blobs ==="

# List all *_1h keys that contain JSON blobs
json_symbols=$(redis-cli keys '*_1h')

for key in $json_symbols; do
  value=$(redis-cli get "$key")
  if [[ "$value" == \{* ]]; then
    echo -e "\n🔸 ${key}:"
    echo "$value" | jq 2>/dev/null || echo "  ⚠️  Malformed JSON"
  fi
done
