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

def test_deposit_and_withdraw():

    # Define variables
    deposit_amount = 5*10**18
    withdraw_amount = 2*10**18

    # deploy etf
    etf_contract = deploy_etf()

    # Deposit as an actual account 
    etf_contract.deposit(
        {"from": accounts[2], "value": deposit_amount}
    )

    # Check balance
    true_deposit_amount, time_last_updated = etf_contract.getUserData(accounts[2])
    assert true_deposit_amount == deposit_amount

    # withdraw
    etf_contract.withdraw(
        withdraw_amount,
        {"from": accounts[2]}
    )

    # check balance
    true_deposit_amount, time_last_updated = etf_contract.getUserData(accounts[2])
    assert true_deposit_amount == deposit_amount - withdraw_amount

def test_calibrate():

    # Wait for the start of a 10 second period so that the calibrate function can be called
    while int(time.time()%10) != 0:
        time.sleep(0.1)

    # Define contracts
    etf_contract = deploy_etf(10, 5, 5*10**18)
    time_of_etf_deployment = time.time()
    token_contract = deploy_token()

    # Define variables
    deposit_amount = 5*10**18
    token_amount = 2*10**18

    # Deposit
    etf_contract.deposit(
        {"from": accounts[2], "value": deposit_amount}
    )

    # Submit token amount
    token_contract.mint(accounts[3], token_amount, {'from': accounts[0]})
    token_contract.approve(etf_contract.address, token_amount, {'from': accounts[3]})
    etf_contract.submitToken(token_contract, token_amount, {'from': accounts[3]})

    # Check token submission
    assert etf_contract.getTotalTokens() == 1
    assert etf_contract.getTokenBalance(token_contract) == token_amount
    assert etf_contract.getTokenAddress(0) == token_contract.address

    # Attemp calibrate
    assert etf_contract.isCalibrationOpen() == True
    amount_withdrawable, can_withdraw, reason = etf_contract.getUserExpectedTokenCalibration(accounts[2], token_contract)
    assert can_withdraw == False
    assert amount_withdrawable == token_amount/2

    # Check token calibration fails (Brownie & pytest revert failing in 1.17.0)
    with brownie.reverts("403: User has not deposited before the previous calibration cycle"):
        etf_contract.calibrateToken(accounts[2], token_contract, {'from': accounts[2]}) 

    # Sleep for 10 seconds to reach next calibaration cycle
    print("Block time: ", token_contract.getTime())
    print("Current Time: ", time.time())
    time.sleep(10)
    # Set a test variable to bring the blocks up to the next calibration cycle (Ganache)
    token_contract.setTest(True)
    print("Block time: ", token_contract.getTime())
    print("Current Time: ", time.time())

    # Check token calibration succeeds
    amount_withdrawable, can_withdraw, reason = etf_contract.getUserExpectedTokenCalibration(accounts[2], token_contract)
    print({"Reason": reason, "Amount withdrawable": amount_withdrawable, "Can withdraw": can_withdraw})
    assert can_withdraw == True
    assert amount_withdrawable == token_amount/2
    etf_contract.calibrateToken(accounts[2], token_contract, {'from': accounts[2]}) 
    assert token_contract.balanceOf(accounts[2]) == token_amount/2

    # Trying to instantluy calibrate again fails
    with brownie.reverts("402: User has allocated tokens before in this calibration cycle"):
        etf_contract.calibrateToken(accounts[2], token_contract, {'from': accounts[2]})

    # Wait for 5 seconds and then isCalibrateOpen should return false
    time.sleep(5)
    token_contract.setTest(False)
    assert etf_contract.isCalibrationOpen() == False

    pass

