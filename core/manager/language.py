
def text(**kwargs):
    var = kwargs

    return {
        'eng': {

            'top_warning': f'This is development version, last update timestamp: ',
            'wallet_comment': 'This is connected to real working EPIC wallet.',
            'top_comments_status': 'Development comments: ',
            'price_card_comment': 'Simple EPIC <-> USD converter, more currencies to be added.',
            'volume_card_comment': 'Total volume from our all assets.',
            'network_card_comment': 'This is connected to EPIC-RADAR node (can be any), '
                                    'If radar node is offline, there is icon indicator, '
                                    'and it connects to explorer API.',
            'asset_table_comment': 'Data collected from exchanges directly, much more details '
                                   'can be added, ideally each asset with separate tab and stats.',
            'top_header_text': '''<span class="h3">
                    <b>Epicentral.io</b><sup><span class="h6">beta</sup> - learn the <b>Epic-Cash</b> blockchain by interacting with the live chain,
                    track node statistics, wallet activity, send or mine coins to learn how to use the technology.
                    Create a wallet and start trading with others on Telegram or raise micro-funding for community events.
                </span>'''
            }
        }