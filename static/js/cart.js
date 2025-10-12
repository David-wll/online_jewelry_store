var updateBtns = document.querySelectorAll('.update-cart')
console.log('📦 Found', updateBtns.length, 'update buttons')

for(var i = 0; i < updateBtns.length; i++){
    updateBtns[i].addEventListener('click', function(e){
        e.preventDefault()
        
        var productId = this.dataset.product
        var action = this.dataset.action
        console.log('🛒 productId:', productId, 'action:', action)
        
        console.log('👤 USER:', user)
        console.log('👤 Checking if user === "AnonymousUser":', user === 'AnonymousUser')
        
        if(user === 'AnonymousUser'){
            console.log('🔴 User is anonymous - calling addCookieItem')
            addCookieItem(productId, action)
        }
        else{
            console.log('🟢 User is logged in - calling updateUserOrder')
            updateUserOrder(productId, action)
        }
    })
}

function addCookieItem(productId, action){
    
    console.log('Not loggeed in...')

    if(action == 'add'){
        if(cart[productId] == undefined){
            cart[productId] = {'quantity':1}
        }
        else{
            cart[productId]['quantity'] += 1
        }
    }
    if(action == 'remove'){
        cart[productId]['quantity'] -= 1

        if(cart[productId]['quantity'] <= 0){
            console.log('Remove item')
            delete cart[productId]
        }
    }
    console.log('cart:', cart)
    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain;path=/"
    location.reload()
}

function updateUserOrder(productId, action){
    console.log('user is logged in, sending data.....')
    
    var url = '/update_item/'
    
    fetch(url, {
        method: 'POST',
        headers:{
            'Content-Type':'application/json',
            'X-CSRFToken':csrftoken,  // ✅ MUST BE CAPITAL 'X'
        },
        body:JSON.stringify({'productId': productId, 'action':action})
    })
    .then((response) => {
        return response.json()
    })
    .then((data) => {
        console.log('data:', data)
        location.reload()
        
    })
}