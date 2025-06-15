// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ArtworkRegistry.sol";

contract ArtworkLicensing {
    enum LicenseType { PERSONAL, COMMERCIAL, EXCLUSIVE }
    
    struct License {
        address licensee;
        uint256 tokenId;
        uint256 startDate;
        uint256 endDate;
        string termsHash;
        LicenseType licenseType;
        bool isActive;
    }

    ArtworkRegistry public artworkRegistry;
    
    mapping(uint256 => License[]) public tokenLicenses;
    mapping(address => mapping(uint256 => uint256)) public licenseIndex;
    mapping(uint256 => address) public currentLicensee;

    event LicenseGranted(uint256 indexed tokenId, address indexed licensee, uint256 startDate, uint256 endDate, string termsHash, LicenseType licenseType);
    event LicenseRevoked(uint256 indexed tokenId, address indexed licensee);

    constructor(address _artworkRegistry) {
        artworkRegistry = ArtworkRegistry(_artworkRegistry);
    }

    function grantLicense(
        uint256 tokenId,
        address licensee,
        uint256 durationInDays,
        string memory termsHash,
        LicenseType licenseType
    ) external {
        require(artworkRegistry.ownerOf(tokenId) == msg.sender, "Not owner");
        require(durationInDays > 0, "Invalid duration");
        
        uint256 startDate = block.timestamp;
        uint256 endDate = startDate + (durationInDays * 1 days);
        
        License memory newLicense = License({
            licensee: licensee,
            tokenId: tokenId,
            startDate: startDate,
            endDate: endDate,
            termsHash: termsHash,
            licenseType: licenseType,
            isActive: true
        });
        
        tokenLicenses[tokenId].push(newLicense);
        licenseIndex[licensee][tokenId] = tokenLicenses[tokenId].length - 1;
        currentLicensee[tokenId] = licensee;
        
        // Update license status in registry
        artworkRegistry.updateLicenseStatus(tokenId, true);
        
        emit LicenseGranted(tokenId, licensee, startDate, endDate, termsHash, licenseType);
    }

    function revokeLicense(uint256 tokenId, address licensee) external {
        require(artworkRegistry.ownerOf(tokenId) == msg.sender, "Not owner");
        uint256 index = licenseIndex[licensee][tokenId];
        License storage license = tokenLicenses[tokenId][index];
        
        require(license.isActive, "License not active");
        license.isActive = false;
        
        if (currentLicensee[tokenId] == licensee) {
            currentLicensee[tokenId] = address(0);
            // Update license status in registry
            artworkRegistry.updateLicenseStatus(tokenId, false);
        }
        
        emit LicenseRevoked(tokenId, licensee);
    }
    // Add these functions to your ArtworkLicensing contract
    function getLicenseCount(uint256 tokenId) public view returns (uint256) {
    return tokenLicenses[tokenId].length;
}

    function getLicenseDetails(uint256 tokenId, uint256 index) public view returns (
        address licensee,
        uint256 startDate,
        uint256 endDate,
        string memory termsHash,
        LicenseType licenseType,
        bool isActive
) {
    require(index < tokenLicenses[tokenId].length, "Invalid license index");
    License memory license = tokenLicenses[tokenId][index];
    return (
        license.licensee,
        license.startDate,
        license.endDate,
        license.termsHash,
        license.licenseType,
        license.isActive
    );
}
}