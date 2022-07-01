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

def test_multi_user_mynt_interactions():

    # Wait for the start of a 10 second period so that the calibrate function can be called
    while int(time.time()%10) != 0:
        time.sleep(0.1)

    # Define variables
    initial_deposit = 5*10**18
    mynt_submission = 3*10**18
    user_1_deposit_amount = 5*10**18
    user_2_deposit_amount = 2*10**18

    # Define contracts
    etf_contract = deploy_etf(10, 5, initial_deposit)
    token_1_contract = deploy_token()

    # Deposit as user 1
    assert accounts[1].balance() == 100*10**18
    etf_contract.deposit(
        {"from": accounts[1], "value": user_1_deposit_amount}
    )
    assert accounts[1].balance() == 100*10**18 - user_1_deposit_amount
    user_1_deposit_by_contract, user_1_last_updated_by_contract = etf_contract.getUserData(accounts[1])
    assert user_1_deposit_by_contract == user_1_deposit_amount

    # Submit MYNT to the ETF
    etf_contract.submitMynt({'from':accounts[9], 'value':mynt_submission})

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
    amount_withdrawable_1, can_withdraw_1, reason = etf_contract.getUserExpectedMyntCalibration(accounts[1])
    assert can_withdraw_1 == True
    assert amount_withdrawable_1 == (mynt_submission)*5/(5+5+2)
    etf_contract.calibrateMynt(accounts[1], {'from': accounts[1]})
    assert accounts[1].balance() == 100*10**18 - user_1_deposit_amount + amount_withdrawable_1 

    # Attempt to calibrate as user 2 fails
    with brownie.reverts("403: User has not deposited before the previous calibration cycle"):
        etf_contract.calibrateMynt(accounts[2], {'from': accounts[2]})
    
    # Check how much user 2 is expected to withdraw in the next calibration cycle
    amount_withdrawable_2, can_withdraw_2, reason = etf_contract.getUserExpectedMyntCalibration(accounts[2])
    assert can_withdraw_2 == False 
    assert amount_withdrawable_2 == (mynt_submission)*2/(5+5+2)

    # User 1 should not be able to calibrate again
    with brownie.reverts("402: User has allocated MYNT before in this calibration cycle"):
        etf_contract.calibrateMynt(accounts[1], {'from': accounts[1]})

    # Wait for 5 seconds and then isCalibrateOpen should return false
    time.sleep(5)
    token_1_contract.setTest(True)
    assert etf_contract.isCalibrationOpen() == False

    # Wait for an additional 5 seconds and then isCalibrateOpen should return true
    time.sleep(5)
    token_1_contract.setTest(False)
    assert etf_contract.isCalibrationOpen() == True

    # User 2 should be able to calibrate; add leeway for check due to accuracy loss
    etf_contract.calibrateMynt(accounts[2], {'from': accounts[2]})
    assert (
        int((accounts[2]).balance() /10**18)
        ==
        int(
            (100*10**18 - user_2_deposit_amount + 
            (( mynt_submission - mynt_submission*5/(5+5+2) )*2/(5+5+2) ))
            /10**18
        )
        
    )

    # User 1 should be able to calibrate again
    amount_withdrawable_3, can_withdraw_3, reason = etf_contract.getUserExpectedMyntCalibration(accounts[1])
    assert can_withdraw_3 == True
    etf_contract.calibrateMynt(accounts[1], {'from': accounts[1]})
    assert (accounts[1]).balance() == 100*10**18 - user_1_deposit_amount + amount_withdrawable_3 + amount_withdrawable_1

    # Withdraw as user 1
    etf_contract.withdraw(user_1_deposit_amount, {'from': accounts[1]})
    assert accounts[1].balance() == 100*10**18 +  amount_withdrawable_3 + amount_withdrawable_1

    # Withdraw as user 2
    etf_contract.withdraw(user_2_deposit_amount, {'from': accounts[2]})

    pass