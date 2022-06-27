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

def test_multi_user_interactions():

    # Wait for the start of a 10 second period so that the calibrate function can be called
    while int(time.time()%10) != 0:
        time.sleep(0.1)

    # Define variables
    initial_deposit = 5*10**18
    first_token_submission = 3*10**18
    user_1_deposit_amount = 5*10**18
    user_2_deposit_amount = 2*10**18

    # Define contracts
    etf_contract = deploy_etf(10, 5, initial_deposit)
    token_1_contract = deploy_token()
    token_2_contract = deploy_token()

    # Deposit as user 1
    assert accounts[1].balance() == 100*10**18
    etf_contract.deposit(
        {"from": accounts[1], "value": user_1_deposit_amount}
    )
    assert accounts[1].balance() == 100*10**18 - user_1_deposit_amount
    user_1_deposit_by_contract, user_1_last_updated_by_contract = etf_contract.getUserData(accounts[1])
    assert user_1_deposit_by_contract == user_1_deposit_amount

    # Submit tokens to ETF
    token_1_contract.mint(accounts[9], first_token_submission, {'from': accounts[0]})
    token_1_contract.approve(etf_contract.address, first_token_submission, {'from': accounts[9]})
    etf_contract.submitToken(token_1_contract, first_token_submission, {'from': accounts[9]})
    assert etf_contract.getTotalTokens() == 1
    assert etf_contract.getTokenBalance(token_1_contract) == first_token_submission
    assert etf_contract.getTokenAddress(0) == token_1_contract.address

    # Wait for 5 seconds as this calibration cycle ends
    time.sleep(5)
    token_1_contract.setTest(True)

    # Deposit as user 2
    assert accounts[2].balance() == 100*10**18
    etf_contract.deposit(
        {"from": accounts[2], "value": user_2_deposit_amount}
    )
    assert accounts[2].balance() == 100*10**18 - user_2_deposit_amount
    user_2_deposit_by_contract, user_2_last_updated_by_contract = etf_contract.getUserData(accounts[2])
    assert user_2_deposit_by_contract == user_2_deposit_amount

    # Wait for 5 seconds as this calibration cycle starts
    time.sleep(5)
    token_1_contract.setTest(False)

    # Calibrate as user 1
    amount_withdrawable, can_withdraw, reason = etf_contract.getUserExpectedTokenCalibration(accounts[1], token_1_contract)
    assert can_withdraw == True
    assert amount_withdrawable == (first_token_submission)*5/(5+5+2)
    etf_contract.calibrateToken(accounts[1], token_1_contract, {'from': accounts[1]})
    assert token_1_contract.balanceOf(accounts[1]) == (first_token_submission)*5/(5+5+2)

    # Attempt to calibrate as user 2 fails
    with brownie.reverts("403: User has not deposited before the previous calibration cycle"):
        etf_contract.calibrateToken(accounts[2], token_1_contract, {'from': accounts[2]})
    
    # Check how much user 2 is expected to withdraw in the next calibration cycle
    amount_withdrawable, can_withdraw, reason = etf_contract.getUserExpectedTokenCalibration(accounts[2], token_1_contract)
    assert can_withdraw == False 
    assert amount_withdrawable == (first_token_submission)*2/(5+5+2)

    # User 1 should not be able to calibrate again
    with brownie.reverts("402: User has allocated tokens before in this calibration cycle"):
        etf_contract.calibrateToken(accounts[1], token_1_contract, {'from': accounts[1]})

    # Wait for 5 seconds and then isCalibrateOpen should return false
    time.sleep(5)
    token_1_contract.setTest(True)
    assert etf_contract.isCalibrationOpen() == False

    # Wait for an additional 5 seconds and then isCalibrateOpen should return true
    time.sleep(5)
    token_1_contract.setTest(False)
    assert etf_contract.isCalibrationOpen() == True

    # User 2 should be able to calibrate
    etf_contract.calibrateToken(accounts[2], token_1_contract, {'from': accounts[2]})
    assert token_1_contract.balanceOf(accounts[2]) == (first_token_submission)*2/(5+5+2)

    # Submit token 2 to ETF
    token_2_contract.mint(accounts[9], first_token_submission, {'from': accounts[0]})
    token_2_contract.approve(etf_contract.address, first_token_submission, {'from': accounts[9]})
    etf_contract.submitToken(token_2_contract, first_token_submission, {'from': accounts[9]})
    assert etf_contract.getTotalTokens() == 2
    assert etf_contract.getTokenBalance(token_2_contract) == first_token_submission
    assert etf_contract.getTokenAddress(1) == token_2_contract.address

    # Calibrate token 2 as user 1
    etf_contract.calibrateToken(accounts[1], token_2_contract, {'from': accounts[1]})
    assert token_2_contract.balanceOf(accounts[1]) == (first_token_submission)*5/(5+5+2)

    # Calibrate token 2 as user 2
    etf_contract.calibrateToken(accounts[2], token_2_contract, {'from': accounts[2]})
    assert token_2_contract.balanceOf(accounts[2]) == (first_token_submission)*2/(5+5+2)