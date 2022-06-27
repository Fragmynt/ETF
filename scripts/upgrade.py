from brownie import networkETF, Contract
from scripts.utils import  get_account, upgrade
from scripts.deploy import deploy_etf_proxy,  deploy_etf
import time

# Get deployment account & transacting account
deployment_owner_account = get_account(1)
test_account = get_account(0)


def deploy_updates(deployment_account, proxy_admin, existing_proxy_address):

    #Step 1: Deploy logic contracts
    new_token =  deploy_etf(deployment_account)
    print("Update new token: ", new_token)

    #Get proxies
    existing_etf_proxy = Contract.from_abi("networkETF", existing_proxy_address, networkETF.abi) 

    #Step 2: upgrade bridge
    upgrade(
        deployment_account,
        existing_etf_proxy,
        new_token,
        proxy_admin_contract=proxy_admin
        )

    pass


def main():

    etf, admin = deploy_etf_proxy(deployment_owner_account)
 
    deploy_updates(deployment_owner_account, admin, etf)

    time.sleep(1)
