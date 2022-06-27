from brownie import Token, networkETF, Contract
from scripts.utils import  encode_function_data, get_account
import time

# Get deployment account & transacting account
deployment_owner_account = get_account(1)
test_account = get_account(0)


def deploy_token(deployment_account):
    deployed_token = Token.deploy(
        {"from": deployment_account}
    )
    
    print("Token deployed...")
    print("Token: ", deployed_token.address)
    print("\n")

    return deployed_token

def deploy_etf(deployment_account):
    deployed_etf = networkETF.deploy(
        {"from": deployment_account}
    )
    deployed_etf.initialize(24*60*60, 60*60, {"from": deployment_account, "value": 10**18})
    
    print("ETF deployed...")
    print("ETF: ", deployed_etf.address)
    print("\n")

    return deployed_etf
    pass

def deploy_etf_proxy(deployment_account):

    #Step 1: Deploy etf
    deployed_etf = deploy_etf(deployment_account)

    #Step  2: Deploy the admin proxy
    proxy_admin = ProxyAdmin.deploy(
       {"from": deployment_account}
    )

    #Step 2: Deploy etf proxy
    etf_proxy = TransparentUpgradeableProxy.deploy(
        deployed_etf.address,
        proxy_admin.address,
        encode_function_data(deployed_etf.initialize, 86400, 3600, 100),
        {"from": deployment_account}
    )

    etf_proxy = Contract.from_abi("etf", etf_proxy.address, deployed_etf.abi)

    print("Proxies deployed...")
    print("Admin Proxy: ", proxy_admin.address)
    print("ETF Proxy: ", etf_proxy.address)
    print("\n")

    return etf_proxy, proxy_admin


def main():
    print("Deployed by: ", deployment_owner_account)
    etf = deploy_etf(deployment_owner_account)
    time.sleep(1)
    pass