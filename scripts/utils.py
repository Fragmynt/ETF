from brownie import accounts, config,  network, Contract

def get_account(num =0 ):
    print("Network: ",  network.show_active())
    if network.show_active() == "development" or network.show_active() == None:
        return accounts[num]
    else:
        if num == 0:
            return  accounts.add(config['wallets']['DEPLOYMENT_PRIVATE'])
        elif num == 1:
            return accounts.add(config['wallets']['OWNER_PRIVATE'])
        else:
            raise Exception('Too High')

def get_current_balance(token, account):
    return token.balanceOf(account)/10**18

def give_tokens(token, owner, skip = 1, account_range = 9):
    for i in range(skip, account_range):
        token.mintTo(get_account(i), 10_000*10**18, {"from": owner})
        
def approve_tokens(token, exchange, owner, skip = 1, account_range=9):
    for i in range(skip, account_range):
        token.mintTo(get_account(i), 1_000_000*10**18, {"from": owner})
        token.approve(exchange, 2**256-1, {"from": get_account(i)})

def encode_function_data(initializer=None, *args):
    """Encodes the function call so we can work with an initializer.
    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: `box.store`.
        Defaults to None.
        args (Any, optional):
        The arguments to pass to the initializer function
    Returns:
        [bytes]: Return the encoded bytes.
    """
    if not len(args): args = b''

    if initializer: return initializer.encode_input(*args)

    return b''


def upgrade(
    account,
    proxy,
    newimplementation_address,
    proxy_admin_contract=None,
    initializer=None,
    *args
):
    transaction = None
    if proxy_admin_contract:
        if initializer:
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy_admin_contract.upgradeAndCall(
                proxy.address,
                newimplementation_address,
                encoded_function_call,
                {"from": account},
            )
        else:
            transaction = proxy_admin_contract.upgrade(
                proxy.address, newimplementation_address, {"from": account}
            )
    else:
        if initializer:
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy.upgradeToAndCall(
                newimplementation_address, encoded_function_call, {"from": account}
            )
        else:
            transaction = proxy.upgradeTo(newimplementation_address, {"from": account})
    return transaction
