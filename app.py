import uuid
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Mock database
PRODUCTS = [
    { 'id': 1, 'name': 'Separating Funnel Pear Shape', 'cat': 'funnel', 'price': 1250, 'caps': ['250ml', '500ml', '1000ml', '2000ml'], 'meta': 'Pear shape · PTFE stopcock', 'desc': 'Our pear-shaped separating funnels are manufactured from high quality borosilicate glass. They are widely used in laboratories for liquid-liquid extraction processes.' },
    { 'id': 2, 'name': 'Borosilicate Beaker Low Form', 'cat': 'beaker', 'price': 360, 'caps': ['100ml', '250ml', '500ml', '1000ml'], 'meta': 'Low form · graduated', 'desc': 'Griffin low-form beakers with printed graduations, made from chemically resistant borosilicate 3.3 glass suitable for heating and general lab use.' },
    { 'id': 3, 'name': 'Round Bottom Flask CORNSIL', 'cat': 'flask', 'price': 1450, 'caps': ['500ml', '1000ml', '2000ml', '5000ml'], 'meta': 'Round shape · single neck', 'desc': 'Round bottom flasks engineered for even heat distribution during distillation, reflux and evaporation applications.' },
    { 'id': 4, 'name': 'Condenser Reflux Liebig', 'cat': 'condenser', 'price': 980, 'caps': ['300mm', '400mm', '500mm'], 'meta': 'Straight jacket · ground joints', 'desc': 'Liebig-style reflux condensers with standard ground glass joints, used to condense vapours back into liquid during reflux reactions.' },
    { 'id': 5, 'name': 'Measuring Cylinder Class A', 'cat': 'cylinder', 'price': 320, 'caps': ['50ml', '100ml', '250ml', '500ml'], 'meta': 'Class A accuracy · hex base', 'desc': 'Class A calibrated measuring cylinders with a hexagonal base for stability, ideal for precise volumetric measurement.' },
    { 'id': 6, 'name': 'Burette with PTFE Stopcock', 'cat': 'burette', 'price': 860, 'caps': ['25ml', '50ml'], 'meta': 'Amber / clear · Class A', 'desc:': 'Precision burettes fitted with a PTFE stopcock for accurate, drip-free titrations in analytical chemistry.' },
    { 'id': 7, 'name': 'Borosilicate Beaker Tall Form', 'cat': 'beaker', 'price': 420, 'caps': ['250ml', '500ml', '1000ml'], 'meta': 'Tall form · spout', 'desc': 'Tall-form Griffin beakers offering a larger height-to-diameter ratio, useful where evaporation surface area needs to be minimised.' },
    { 'id': 8, 'name': 'Separating Funnel with PTFE Stopcock', 'cat': 'funnel', 'price': 1450, 'caps': ['500ml', '1000ml'], 'meta': 'Pear shape · heavy duty', 'desc': 'Heavy duty separating funnels with a PTFE stopcock offering superior chemical resistance for aggressive solvents.' },
    { 'id': 9, 'name': 'Reactor Assembly CORNSIL', 'cat': 'reactor', 'price': 4200, 'caps': ['1L', '2L', '5L'], 'meta': 'Jacketed · multi-neck', 'desc': 'Jacketed glass reactor assemblies used for controlled-temperature chemical synthesis in research and pilot-scale industry.' },
    { 'id': 10, 'name': 'Distillation Assembly CORNSIL', 'cat': 'assembly', 'price:': 2650, 'caps': ['Standard', 'Steam', 'Vacuum'], 'meta': 'Complete glass assembly', 'desc': 'Complete distillation glass assemblies including flask, condenser and receiver, built to standard ground joints.' },
    { 'id': 11, 'name': 'Borosilicate Beaker Griffin', 'cat': 'beaker', 'price': 480, 'caps': ['500ml', '1000ml'], 'meta': 'Griffin low form · spout', 'desc': 'General purpose Griffin beakers ideal for mixing, heating and transporting laboratory liquids.' },
    { 'id': 12, 'name': 'Kjeldahl Distillation Unit', 'cat': 'assembly', 'price': 1980, 'caps': ['Standard'], 'meta': 'Water distillation · 0-5kW', 'desc': 'CORNSIL Kjeldahl distillation unit for water/ammonia distillation applications in analytical laboratories.' }
]

orders_db = {}
contact_requests = []
custom_requests = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(PRODUCTS), 200

@app.route('/api/checkout', methods=['POST'])
def handle_checkout():
    data = request.json
    cart = data.get('cart', [])
    user_info = data.get('userInfo', {})
    
    order_id = str(uuid.uuid4())[:8].upper()
    order_data = {
        'order_id': order_id,
        'user_info': user_info,
        'cart': cart,
        'status': 'Processing'
    }
    orders_db[order_id] = order_data
    
    print(f"\n[ORDER RECEIVED] ID: {order_id}")
    print(f"Customer: {user_info.get('name')} | Total items: {len(cart)}")
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'message': 'Order placed successfully!'
    }), 200

@app.route('/api/track_order/<order_id>', methods=['GET'])
def track_order(order_id):
    order = orders_db.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
        
    return jsonify({
        'order_id': order_id,
        'status': order['status'],
        'items_count': len(order['cart'])
    }), 200

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.json
    contact_requests.append(data)
    print(f"\n[CONTACT FORM] New message from {data.get('name')} ({data.get('email')})")
    print(f"Message: {data.get('message')}")
    return jsonify({'success': True, 'message': 'Message sent! We will get back to you shortly.'}), 200

@app.route('/api/custom', methods=['POST'])
def handle_custom():
    data = request.json
    custom_requests.append(data)
    print(f"\n[CUSTOM QUOTE] Request from {data.get('name')}")
    print(f"Requirement: {data.get('details')}")
    return jsonify({'success': True, 'message': 'Custom manufacturing request submitted!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
