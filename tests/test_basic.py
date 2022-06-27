import pytest, brownie, time 
from brownie import accounts, networkETF, Token


def deploy_etf(cycle_period = 24*60*60, cycle_length = 60*60, bond_amount =100):
    # deploy etf
    etf_contract = networkETF.deploy({'from': accounts[0]})
    etf_contract.initialize(cycle_period, cycle_length, {'from': accounts[0], 'value':bond_amount})
    return etf_contract

def deploy_token():
    # deploy token
    token_contract = Token.deploy({'from': accounts[0]})
    token_contract.initialize({'from': accounts[0]})
    return token_contract


# Try to deploy & initialize a new ETF again
def test_deploy_and_dual_init():

    # Define contracts
    etf_contract = deploy_etf()

    with brownie.reverts("Initializable: contract is already initialized"):
        etf_contract.initialize(24*60*60, 60*60, {'from': accounts[0], 'value':100})


# Try to pause and unpause the ETF
def test_pause_and_unpause():

    # Define contracts
    etf_contract = deploy_etf()

    # Pause the ETF
    etf_contract.pause({'from': accounts[0]})

    # Check that the ETF is paused
    assert etf_contract.paused() == True

    # Try to deposit
    with brownie.reverts("Pausable: paused"):
        etf_contract.deposit(
            {"from": accounts[2], "value": 5*10**18}
        )

    # Unpause the ETF
    etf_contract.unpause({'from': accounts[0]})

    # Now try to deposit again
    etf_contract.deposit(
        {"from": accounts[2], "value": 5*10**18}
    )
    assert etf_contract.getUserData(accounts[2])[0] == 5*10**18

    # Check that the ETF is not paused
    assert etf_contract.paused() == False

    # Try pausing as a non-owner
    with brownie.reverts("Ownable: caller is not the owner"):
        etf_contract.pause({'from': accounts[1]})

    # Transfer ownership to a new account
    etf_contract.transferOwnership(accounts[1], {'from': accounts[0]})

    # Try pausing as a new owner
    etf_contract.pause({'from': accounts[1]})
    assert etf_contract.paused() == True