// SPDX-License-Identifier: UNLICENSED
/* 
@notice The code is proprietary & cannot be copied, re-used or deployed without the 
		express permission of Fragmynt, Inc.
*/

pragma solidity ^0.8.10;

import {fMathUD60x18, fMath} from "./fMathUD60x18.sol";

library fMathPool {

    /*
    @notice Takes in a space & gives it's price based on 1.0001^space
    @param space_ int space
    @param negative_number if space is a negative number
    @returns price at space in uint256 60x18
    */
    function get_price_from_space( int256 space_) internal pure returns(fMath.UD60x18 memory) {
        
        uint256 _abs_space= get_abs_value(space_) ;

        fMath.UD60x18 memory num_1_0001;
        num_1_0001.value = 1000100000000000000;

        fMath.UD60x18 memory result = fMathUD60x18.powu(num_1_0001,_abs_space);
        if (bool(0>space_)) result = fMathUD60x18.div(fMathUD60x18.scale(), result);
        return result;
    }

    /*
    @notice returns int as uint256
    @param x an int to be converted to uint256
    @returns uint256 absolute value
    */ 
    function get_abs_value(int x) internal pure returns (uint) {
    	return uint256(x >= 0 ? x : -x);
    }  

	/* 
	@notice intakes two fmath60x18 structs and returns a bool if first is greater
	@param x value 1
	@param y value 2
	@return is_greater bool true if x > y
    */
	function is_greater(fMath.UD60x18 memory x, fMath.UD60x18 memory y) internal pure returns(bool) {
        uint x_replica = uint(x.value);
        uint y_replica = uint(y.value);
        if (x_replica > y_replica) return true;
        else return false;
	}


    /* 
	@notice intakes two fmath60x18 structs and returns a bool if first is greater
	@param x value 1
	@param y value 2
	@return is_greater bool true if x > y
    */
	function is_greater_or_equal(fMath.UD60x18 memory x, fMath.UD60x18 memory y) internal pure returns(bool greater) {
		return (x.value >= y.value);
	}

    /* 
	@notice intakes two fmath60x18 structs and returns a bool if first is greater
	@param x value 1
	@param y value 2
	@return is_greater bool true if x > y
    */
	function is_equal(fMath.UD60x18 memory x, fMath.UD60x18 memory y) internal pure returns(bool greater) {
		return (x.value == y.value); 
	}


	/*
    @notice converts a uint256 into a 60x18 number. E.g. input 1 and get 1x18(0)
    @param number_ the number to convert
    @returns a uint256 as a 60x18
    */ 
    function from_uint_to_60x18(uint256 number_) internal pure returns(fMath.UD60x18 memory) {
        return fMathUD60x18.fromUint( number_ );
    }

    function from_base_to_60x18(uint256 number_) internal pure returns(fMath.UD60x18 memory) {
        return fMathUD60x18.div(fMathUD60x18.fromUint( number_ ), fMathUD60x18.fromUint( 10**18 ));
    }
	
    function from_decimal_to_60x18(uint256 number_, uint decimals_) internal pure returns(fMath.UD60x18 memory) {
        return fMathUD60x18.div(fMathUD60x18.fromUint( number_ ), fMathUD60x18.fromUint( 10**decimals_ ));
    }

    function to_uint(fMath.UD60x18 memory x) internal pure returns (uint){
        return x.value;
    }
}