const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // 1. Deploy ArtworkRegistry
  const ArtworkRegistry = await ethers.getContractFactory("ArtworkRegistry");
  const registry = await ArtworkRegistry.deploy();
  await registry.waitForDeployment(); // Changed from .deployed()
  console.log("ArtworkRegistry deployed to:", await registry.getAddress());

  // 2. Deploy ArtworkLicensing
  const ArtworkLicensing = await ethers.getContractFactory("ArtworkLicensing");
  const licensing = await ArtworkLicensing.deploy(await registry.getAddress());
  await licensing.waitForDeployment();
  console.log("ArtworkLicensing deployed to:", await licensing.getAddress());

  // 3. Configure licensing contract in registry
  const setLicensingTx = await registry.setLicensingContract(await licensing.getAddress());
  await setLicensingTx.wait();
  console.log("Licensing contract set in registry");

  // Save addresses
  const contracts = {
    registry: await registry.getAddress(),
    licensing: await licensing.getAddress(),
    network: "localhost"
  };

  fs.writeFileSync("contract-addresses.json", JSON.stringify(contracts, null, 2));
  console.log("Contract addresses saved to contract-addresses.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });