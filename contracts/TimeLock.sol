// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TimeLock {
    address public beneficiary;
    uint256 public releaseTime;
    
    constructor(address _beneficiary, uint256 _releaseTime) {
        require(_releaseTime > block.timestamp, "Invalid release time");
        beneficiary = _beneficiary;
        releaseTime = _releaseTime;
    }
    
    function withdraw() public {
        require(block.timestamp >= releaseTime, "Too early");
        require(msg.sender == beneficiary, "Not beneficiary");
        
        uint256 amount = address(this).balance;
        payable(beneficiary).transfer(amount);
    }
    
    receive() external payable {}
}