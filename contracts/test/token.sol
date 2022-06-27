// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "../../node_modules/@openzeppelin/contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";
import "../../node_modules/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "../../node_modules/@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract Token is Initializable, ERC20Upgradeable, OwnableUpgradeable {
    function initialize() initializer public {
        __ERC20_init("testToken", "TK");
        __Ownable_init();
    }

    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
    function mintTo(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
    ///////////////////////////////////////////////////////////////////////////////////////////
    function getTime() public view returns (uint) {
        return block.timestamp;
    }
    bool public test;
    function setTest(bool test_) public {
        test = test_;
    }
}