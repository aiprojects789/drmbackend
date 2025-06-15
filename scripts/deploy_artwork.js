const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  
  console.log("Deploying artwork contracts with account:", deployer.address);

  // 1. Deploy ArtworkRegistry
  const ArtworkRegistry = await hre.ethers.getContractFactory("ArtworkRegistry");
  const registry = await ArtworkRegistry.deploy();
  await registry.waitForDeployment();
  console.log("ArtworkRegistry deployed to:", await registry.getAddress());

  // 2. Deploy ArtworkLicensing
  const ArtworkLicensing = await hre.ethers.getContractFactory("ArtworkLicensing");
  const licensing = await ArtworkLicensing.deploy();
  await licensing.waitForDeployment();
  console.log("ArtworkLicensing deployed to:", await licensing.getAddress());

  // 3. Deploy RoyaltyDistributor (requires token address)
  const paymentTokenAddress = "0xYourTokenAddress"; // Replace with your token address
  const RoyaltyDistributor = await hre.ethers.getContractFactory("RoyaltyDistributor");
  const royalty = await RoyaltyDistributor.deploy(
    deployer.address, // Marketplace address (temporary)
    paymentTokenAddress
  );
  await royalty.waitForDeployment();
  console.log("RoyaltyDistributor deployed to:", await royalty.getAddress());

  // Save addresses
  const contracts = {
    registry: await registry.getAddress(),
    licensing: await licensing.getAddress(),
    royalty: await royalty.getAddress(),
    network: hre.network.name
  };
  
  const fs = require("fs");
  fs.writeFileSync("contract-addresses.json", JSON.stringify(contracts, null, 2));
  console.log("Contract addresses saved to contract-addresses.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });