// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.4;

import {fMath, fMathUD60x18, fMathPool} from "../math/fMathPool.sol";

library nETFStructs {
    
    struct nETFToken {
        fMath.UD60x18 deposit;
        uint lastUpdated;
       
        //Allocation checks for every cycle
        uint timeMyntAllocated;
        mapping(address => uint) timeTokenAllocated;
    }


    enum STATUS {UNITIALIZED, INITIALIZED, PAUSED}
    struct nFundManager {
        uint cyclePeriod;
        uint cycleLength;   
        
        fMath.UD60x18 myntDeposited;
        mapping(address => nETFToken) users;

        //This is for contract utility 
        uint totalTokensAvailable;
        mapping(uint => address) tokenNumberToAddress;
        mapping(address => bool) tokenExists;

        //This mynt balance is as received from other contracts for the current cycle
        fMath.UD60x18 myntBalance;
        fMath.UD60x18 myntBondsUsed;
        uint myntLastUpdated;

        mapping(address => fMath.UD60x18) tokenBalances;
        mapping(address => fMath.UD60x18) tokenBondsUsed;
        mapping(address => uint) tokenLastUpdated;
    }

}