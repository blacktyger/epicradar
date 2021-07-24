
liquidity = """
query($pool_address: String!)
{ethereum(network: bsc){
    address(address: {is: $pool_address}){
        balances {
            currency {
                symbol
            }
            value
    }}
}}"""


pool_volume = """
query($pool_address: String!, $date_start: ISO8601DateTime!, $date_stop: ISO8601DateTime!)
{ethereum (network: bsc){
    dexTrades(
        options: {desc: "count"}, 
        smartContractAddress:{is: $pool_address},
        date: {since: $date_start, till: $date_stop}
    ){
        count
        tradeAmount(in:USD)
    }}
}"""


ohlc = """
query($base: String!, $quote: String!)
{ethereum(network: bsc){
    dexTrades(options: {limit: 200, asc: "timeInterval.minute"},
    date: {since:"2021-05-10"}
    baseCurrency: {is: $base},
    quoteCurrency: {is: $quote}){
        timeInterval {
            minute(count: 60)
        }
        baseCurrency {
            symbol
        }
        quoteCurrency {
            symbol
        }
        close_price: maximum(of: block get: quote_price)
    }}
}
"""