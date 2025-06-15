// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PaymentSplitter {
    address[] public payees;
    mapping(address => uint256) public shares;
    uint256 public totalShares;
    
    constructor(address[] memory _payees, uint256[] memory _shares) {
        require(_payees.length == _shares.length, "Invalid input");
        
        for (uint i = 0; i < _payees.length; i++) {
            _addPayee(_payees[i], _shares[i]);
        }
    }
    
    receive() external payable {
        distribute();
    }
    
    function distribute() public {
        uint256 balance = address(this).balance;
        for (uint i = 0; i < payees.length; i++) {
            address payee = payees[i];
            uint256 share = balance * shares[payee] / totalShares;
            payable(payee).transfer(share);
        }
    }
    
    function _addPayee(address account, uint256 share) private {
        require(account != address(0), "Invalid address");
        require(share > 0, "Share must be positive");
        
        payees.push(account);
        shares[account] = share;
        totalShares += share;
    }
}