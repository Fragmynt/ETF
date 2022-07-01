// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.4;

import {IERC20} from "./utils/interfaces/IERC20.sol";
import {fMath, fMathUD60x18, fMathPool} from "./utils/math/fMathPool.sol";
import {nETFStructs} from "./utils/struct/fStruct.sol";
import {ContextUpgradeable} from "../node_modules/@openzeppelin/contracts-upgradeable/utils/ContextUpgradeable.sol";
import {PausableUpgradeable} from "../node_modules/@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";
import {Initializable} from "../node_modules/@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import {OwnableUpgradeable} from "../node_modules/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract networkETF is Initializable, ContextUpgradeable, OwnableUpgradeable, PausableUpgradeable {

    event Deposit(address indexed user,uint timestamp, uint amount);
    event Withdraw(address indexed user, uint timestamp, uint amount);
    event CalibrateToken(address indexed user, uint timestamp, address indexed tokenAddress, uint amount);
    event CalibrateMynt(address indexed user, uint timestamp, uint amount);
    event SubmitToken(address indexed provider, uint timestamp, address indexed tokenAddress, uint amount);
    event SubmitMynt(address indexed provider, uint timestamp, uint amount);

    nETFStructs.nFundManager private fundManager;


    function initialize(uint cyclePeriod, uint cycleLength) initializer public payable {
        
        require(msg.value > 0, "400: Initialization requires a non-zero deposit");

        fundManager.cyclePeriod = cyclePeriod;
        fundManager.cycleLength = cycleLength;

         //Set bonds for fund & user
        fundManager.users[_msgSender()].deposit =  fMathPool.from_base_to_60x18(msg.value);
        fundManager.users[_msgSender()].lastUpdated = block.timestamp;

        fundManager.myntDeposited =  fMathPool.from_base_to_60x18(msg.value);

        __Ownable_init();
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function deposit() whenNotPaused() public payable returns(bool) {

        require(msg.value > 0, "400: Invalid amount");

        //Set bonds for fund & user
        fundManager.users[_msgSender()].deposit = fMathUD60x18.add(fundManager.users[_msgSender()].deposit, fMathPool.from_base_to_60x18(msg.value));
        fundManager.users[_msgSender()].lastUpdated = block.timestamp;
        fundManager.myntDeposited = fMathUD60x18.add(fundManager.myntDeposited, fMathPool.from_base_to_60x18(msg.value));

        //Log event
        emit Deposit(_msgSender(), block.timestamp, msg.value);

        return true;
    }

    function withdraw(uint amount_) whenNotPaused() public payable returns(bool){

        require(amount_ > 0, "400: Invalid amount");
        require(amount_ <= fMathPool.to_uint(fundManager.users[_msgSender()].deposit), "401: Insufficient amount deposited");

        //Set bonds for fund & user
        fundManager.users[_msgSender()].deposit = fMathUD60x18.sub(fundManager.users[_msgSender()].deposit, fMathPool.from_base_to_60x18(amount_));
        fundManager.users[_msgSender()].lastUpdated = block.timestamp;
        fundManager.myntDeposited = fMathUD60x18.sub(fundManager.myntDeposited, fMathPool.from_base_to_60x18(amount_));

        // Send funds to user
        payable(_msgSender()).transfer(amount_);

        //Log event
        emit Withdraw(_msgSender(), block.timestamp, amount_);

        return true;
    }


    function calibrateToken(address user, address token) whenNotPaused() public {

        // Check & update token data if necessary
        // Update token data for cycle
        uint tokenLastUpdated = fundManager.tokenLastUpdated[token];
        //If cycle bonds have not been allocated for this token yet, set to 0
        if (tokenLastUpdated < (block.timestamp - fundManager.cycleLength)) {
            fundManager.tokenBondsUsed[token] = fMathUD60x18.fromUint(0);
        }
        fundManager.tokenLastUpdated[token] = block.timestamp;

        //Ensure withdrawable is true
        (fMath.UD60x18 memory userWithdrawableAmount, bool isWithdrawable, string memory reason) = _getUserExpectedTokenCalibration( user,  token);
        require(isWithdrawable, reason);

        IERC20(token).transfer(user, fMathPool.to_uint(userWithdrawableAmount) );

        // Update user's time token allocated & token data
        fundManager.users[user].timeTokenAllocated[token] = block.timestamp;    
        fundManager.tokenBondsUsed[token] = fMathUD60x18.add(fundManager.tokenBondsUsed[token], fundManager.users[user].deposit);
        fundManager.tokenBalances[token] = fMathUD60x18.sub(fundManager.tokenBalances[token], userWithdrawableAmount);

        //Log event
        emit CalibrateToken(user, block.timestamp, token, fMathPool.to_uint(userWithdrawableAmount));

    } 

    function calibrateMynt(address payable user) whenNotPaused() public payable {

        // Check & update MYNT data if necessary
        // Update MYNT data for cycle
        uint myntLastUpdated = fundManager.myntLastUpdated;
        //If cycle bonds have not been allocated for this token yet, set to 0
        if (myntLastUpdated < (block.timestamp - fundManager.cycleLength)) {
            fundManager.myntBondsUsed = fMathUD60x18.fromUint(0);
        }
        fundManager.myntLastUpdated = block.timestamp;

        //Ensure withdrawable is true
        (fMath.UD60x18 memory userWithdrawableAmount, bool isWithdrawable, string memory reason) =_getUserExpectedMyntCalibration( user);
        require(isWithdrawable, reason);

        //Return user the tokens based on existing bonds, and update their timeTokenAllocated
        user.transfer(fMathPool.to_uint(userWithdrawableAmount));

        //Update user's time MYNT allocated & MYNT data
        fundManager.users[user].timeMyntAllocated = block.timestamp;
        fundManager.myntBondsUsed = fMathUD60x18.add(fundManager.myntBondsUsed, fundManager.users[user].deposit);
        fundManager.myntBalance = fMathUD60x18.sub(fundManager.myntBalance, userWithdrawableAmount);

        //Log event
        emit CalibrateMynt(user, block.timestamp, fMathPool.to_uint(userWithdrawableAmount));
    }

    function submitToken(address token, uint amount) whenNotPaused() public {

        //Require amount > 0
        require(amount > 0, "401: Amount must be greater than 0");

        // Ensure token has 18 
        require(IERC20(token).decimals() == 18, "402: Token must have 18 decimals");

        //Transfer the token from the protocol
        IERC20(token).transferFrom(_msgSender(), address(this), amount);

        //Check if tokenExists, if not add to total & give uint
        if (!fundManager.tokenExists[token]) {
            fundManager.tokenExists[token] = true;
            fundManager.tokenNumberToAddress[fundManager.totalTokensAvailable]= token;
            fundManager.totalTokensAvailable += 1;  
        } 

        //Update token data
        fundManager.tokenBalances[token] = fMathUD60x18.add(fundManager.tokenBalances[token], fMathPool.from_base_to_60x18(amount));

        //Log event
        emit SubmitToken(_msgSender(), block.timestamp, token, amount);
    }

    function submitMynt() whenNotPaused() public payable {
        //Require msg value > 0
        require(msg.value > 0, "401: Amount must be greater than 0");

        //Update MYNT data
        fundManager.myntBalance = fMathUD60x18.add(fundManager.myntBalance, fMathPool.from_base_to_60x18(msg.value));

        //Log event
        emit SubmitMynt(_msgSender(), block.timestamp, msg.value);
    }


    ////////////////////////////////////////////////////////////////////////////////

    function getTotalTokens() public view returns (uint) {
        return fundManager.totalTokensAvailable;
    }

    function getTokenAddress(uint tokenNumber) public view returns (address) {
        return fundManager.tokenNumberToAddress[tokenNumber];
    }

    function getTotalMyntDeposit() public view returns (uint) {
        return fMathPool.to_uint(fundManager.myntDeposited);
    }

    function getTokenBalance(address token) public view returns (uint) {
        return fMathPool.to_uint(fundManager.tokenBalances[token]);
    }

    function getMyntBalance() public view returns (uint) {
        return fMathPool.to_uint(fundManager.myntBalance);
    }

    function isCalibrationOpen() public view returns (bool) {
        return (block.timestamp % fundManager.cyclePeriod) < fundManager.cycleLength;
    }

    function getUserData(address user) public view returns (uint, uint) {
        return (fMathPool.to_uint(fundManager.users[user].deposit), fundManager.users[user].lastUpdated);
    }

    function getUserExpectedTokenCalibration(address user, address token) public view 
    returns (uint amount, bool canWithdraw, string memory reason) {
        fMath.UD60x18 memory amount_ud60x18;
        (amount_ud60x18, canWithdraw, reason) = _getUserExpectedTokenCalibration(user, token);
        return (fMathPool.to_uint(amount_ud60x18), canWithdraw, reason);
    }

    function getUserExpectedMyntCalibration(address user) public view 
    returns (uint amount, bool canWithdraw, string memory reason) {
        fMath.UD60x18 memory amount_ud60x18;
        (amount_ud60x18, canWithdraw, reason) = _getUserExpectedMyntCalibration(user);
        return (fMathPool.to_uint(amount_ud60x18), canWithdraw, reason);
    }


    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    function _getUserExpectedTokenCalibration(address user, address token) internal view 
    returns (
        fMath.UD60x18 memory amount,
        bool canWithdraw, 
        string memory reason
    ) {

        // Check & update token data if necessary
        // Update token data for cycle
        uint tokenLastUpdated = fundManager.tokenLastUpdated[token];
        fMath.UD60x18 memory tokenBondsUsed = fundManager.tokenBondsUsed[token];
        //If cycle bonds have not been allocated for this token yet, set to 0
        if (tokenLastUpdated < (block.timestamp - fundManager.cycleLength)) {
            tokenBondsUsed = fMathUD60x18.fromUint(0);
        }
        
        canWithdraw = true;
        //Ensure calibration cycle is open
        if (!isCalibrationOpen()) {
            canWithdraw = false;
            reason = "401: Calibration cycle is closed";
        }
        //Ensure user has deposited before the previous calibration cycle
        if( fundManager.users[user].lastUpdated >(block.timestamp - fundManager.cyclePeriod)){
            canWithdraw = false;
            reason = "403: User has not deposited before the previous calibration cycle";
        }

        //Ensure time timeTokenAllocated is before the previous calibration length
        if(fundManager.users[user].timeTokenAllocated[token] > 
        (block.timestamp - fundManager.cycleLength)){
            canWithdraw = false;
            reason = "402: User has allocated tokens before in this calibration cycle";
        }

        // Ensure user has deposited > 0
        if ( fMathPool.to_uint(fundManager.users[user].deposit) == 0) {
            canWithdraw = false;
            reason = "404: User has not deposited any MYNT";
        }

        //Return user the tokens based on existing bonds, and update their timeTokenAllocated
        fMath.UD60x18 memory userBonds = fundManager.users[user].deposit;
        fMath.UD60x18 memory totalTokenBonds = fMathUD60x18.sub(fundManager.myntDeposited, tokenBondsUsed);
        fMath.UD60x18 memory tokenAvailable = fundManager.tokenBalances[token];
        
        amount = fMathUD60x18.div(fMathUD60x18.mul(userBonds, tokenAvailable), totalTokenBonds);  

        return (amount, canWithdraw, reason);

    }

    function _getUserExpectedMyntCalibration(address user) internal view
    returns (
        fMath.UD60x18 memory amount,
        bool canWithdraw,
        string memory reason
    ) {
            // Check & update token data if necessary
            // Update token data for cycle
            uint tokenLastUpdated = fundManager.myntLastUpdated;
            fMath.UD60x18 memory myntBondsUsed = fundManager.myntBondsUsed;
            //If cycle bonds have not been allocated for this token yet, set to 0
            if (tokenLastUpdated < (block.timestamp - fundManager.cycleLength)) {
                myntBondsUsed = fMathUD60x18.fromUint(0);
            }

            canWithdraw = true; 
            //Ensure calibration cycle is open
            if (!isCalibrationOpen()) {
                canWithdraw = false;
                reason = "401: Calibration cycle is closed";
            }
            //Ensure user has deposited before the previous calibration cycle
            if( fundManager.users[user].lastUpdated >
            (block.timestamp - fundManager.cyclePeriod)){
                canWithdraw = false;
                reason = "403: User has not deposited before the previous calibration cycle";
            }
            //Ensure time timeTokenAllocated is before the previous calibration length
            if(fundManager.users[user].timeMyntAllocated >
            (block.timestamp - fundManager.cycleLength)){
                canWithdraw = false;
                reason = "402: User has allocated MYNT before in this calibration cycle";
            }

            // Ensure user has deposited > 0
            if ( fMathPool.to_uint(fundManager.users[user].deposit) == 0) {
                canWithdraw = false;
                reason = "404: User has not deposited any MYNT";
            }

            //Return user the tokens based on existing bonds, and update their timeTokenAllocated
            fMath.UD60x18 memory userBonds = fundManager.users[user].deposit;
            fMath.UD60x18 memory totalMYNTBonds = fMathUD60x18.sub(fundManager.myntDeposited, myntBondsUsed);
            fMath.UD60x18 memory myntAvailable = fundManager.myntBalance;

            amount = fMathUD60x18.div(fMathUD60x18.mul(userBonds, myntAvailable), totalMYNTBonds);
            
            return (amount, canWithdraw, reason);
    }

    uint[50] __gap;

}