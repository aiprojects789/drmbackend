// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Hello {
    string public greeting;
    
    constructor() {
        greeting = "Hello, Hardhat 2.24!";
    }
    
    function getGreeting() public view returns (string memory) {
        return greeting;
    }
}