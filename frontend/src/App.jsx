import './App.css'
import PayPalButton from './components/PayPalButton'

function App() {
  return (
    <div style={{ padding: "40px", textAlign: "center" }}>
      <h1>Checkout Page</h1>
      <p>Select PayPal to complete your payment.</p>

      {/* PayPal Integration */}
      <div style={{ marginTop: "20px" }}>
        <PayPalButton amount="10.00" />
      </div>
    </div>
  )
}

export default App
