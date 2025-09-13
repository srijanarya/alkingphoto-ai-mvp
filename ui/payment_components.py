"""
TalkingPhoto AI MVP - Payment UI Components for Streamlit
Streamlit-compatible payment flow and subscription management
"""

import streamlit as st
import time
import qrcode
import io
import base64
from typing import Dict, List, Optional
from services.payment_service import payment_service, SubscriptionTier, PricingPlan
from ui_theme import create_feature_card, create_status_badge


class PaymentUI:
    """Payment UI components for Streamlit"""
    
    @staticmethod
    def render_pricing_cards():
        """Render pricing tier cards"""
        st.markdown("""
        <div style='margin: 3rem 0 2rem 0; text-align: center;'>
            <h2 style='color: #ece7e2; font-size: 2.5rem; margin-bottom: 1rem;'>Choose Your Plan</h2>
            <p style='color: #7b756a; font-size: 1.2rem;'>Unlock unlimited creativity with our flexible pricing</p>
        </div>
        """, unsafe_allow_html=True)
        
        plans = payment_service.pricing_plans
        
        # Create columns for pricing cards
        cols = st.columns(4)
        
        for idx, (tier, plan) in enumerate(plans.items()):
            with cols[idx]:
                PaymentUI._render_pricing_card(plan, tier == SubscriptionTier.PRO)
    
    @staticmethod
    def _render_pricing_card(plan: PricingPlan, is_featured: bool = False):
        """Render individual pricing card"""
        card_style = "border: 2px solid #d96833;" if is_featured else ""
        featured_badge = "🔥 Most Popular" if is_featured else ""
        
        # Calculate yearly savings
        yearly_savings = (plan.price_monthly * 12) - plan.price_yearly
        savings_percentage = int((yearly_savings / (plan.price_monthly * 12)) * 100) if plan.price_monthly > 0 else 0
        
        features_html = "".join([f"<li style='margin: 0.5rem 0; color: #7b756a;'>✅ {feature}</li>" 
                                for feature in plan.features])
        
        st.markdown(f"""
        <div class="feature-card" style="{card_style} position: relative;">
            {f'<div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #d96833; color: white; padding: 0.3rem 1rem; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">{featured_badge}</div>' if featured_badge else ''}
            
            <div style="text-align: center; margin-bottom: 2rem;">
                <h3 style="color: #d96833; font-size: 1.8rem; margin-bottom: 0.5rem;">{plan.name}</h3>
                
                {f'<div style="font-size: 3rem; font-weight: 900; color: #ece7e2; margin: 1rem 0;">${plan.price_monthly:.0f}</div>' if plan.price_monthly > 0 else '<div style="font-size: 3rem; font-weight: 900; color: #ece7e2; margin: 1rem 0;">Free</div>'}
                
                {f'<p style="color: #7b756a;">per month</p>' if plan.price_monthly > 0 else '<p style="color: #7b756a;">forever</p>'}
                
                {f'<p style="color: #d96833; font-size: 0.9rem; margin-top: 0.5rem;">or ${plan.price_yearly:.0f}/year (Save {savings_percentage}%)</p>' if plan.price_yearly > 0 and savings_percentage > 0 else ''}
                
                <div style="background: rgba(217,104,51,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    <div style="font-size: 2rem; font-weight: bold; color: #d96833;">{plan.credits_monthly}</div>
                    <p style="color: #7b756a; margin: 0;">videos per month</p>
                </div>
            </div>
            
            <ul style="list-style: none; padding: 0; margin: 1.5rem 0;">
                {features_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Add action buttons
        if plan.tier == SubscriptionTier.FREE:
            if st.button("Current Plan", key=f"btn_{plan.tier.value}", disabled=True):
                pass
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Monthly ${plan.price_monthly:.0f}", key=f"monthly_{plan.tier.value}"):
                    PaymentUI.handle_subscription_selection(plan.tier, "monthly")
            with col2:
                if st.button(f"Yearly ${plan.price_yearly:.0f}", key=f"yearly_{plan.tier.value}"):
                    PaymentUI.handle_subscription_selection(plan.tier, "yearly")
    
    @staticmethod
    def handle_subscription_selection(tier: SubscriptionTier, billing_cycle: str):
        """Handle subscription plan selection"""
        st.session_state.selected_tier = tier
        st.session_state.selected_billing = billing_cycle
        st.session_state.show_payment_form = True
        st.rerun()
    
    @staticmethod
    def render_credit_purchase():
        """Render credit purchase interface"""
        st.markdown("""
        <div style='margin: 3rem 0 2rem 0; text-align: center;'>
            <h2 style='color: #ece7e2; font-size: 2rem; margin-bottom: 1rem;'>Buy Additional Credits</h2>
            <p style='color: #7b756a; font-size: 1.1rem;'>Need more videos? Purchase credits as you go</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Credit packages
        credit_packages = [
            {"credits": 10, "price": 9.99, "bonus": 0, "popular": False},
            {"credits": 25, "price": 22.99, "bonus": 2, "popular": True},
            {"credits": 50, "price": 42.99, "bonus": 5, "popular": False},
            {"credits": 100, "price": 79.99, "bonus": 15, "popular": False},
        ]
        
        cols = st.columns(4)
        
        for idx, package in enumerate(credit_packages):
            with cols[idx]:
                PaymentUI._render_credit_package(package)
    
    @staticmethod
    def _render_credit_package(package: Dict):
        """Render individual credit package"""
        total_credits = package["credits"] + package["bonus"]
        price_per_credit = package["price"] / total_credits
        
        card_style = "border: 2px solid #d96833;" if package["popular"] else ""
        popular_badge = "💎 Best Value" if package["popular"] else ""
        
        st.markdown(f"""
        <div class="feature-card" style="{card_style} position: relative; text-align: center;">
            {f'<div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #d96833; color: white; padding: 0.3rem 1rem; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">{popular_badge}</div>' if popular_badge else ''}
            
            <div style="font-size: 2.5rem; font-weight: 900; color: #ece7e2; margin: 1rem 0;">{package["credits"]}</div>
            <p style="color: #7b756a; margin: 0;">Base Credits</p>
            
            {f'<div style="color: #d96833; font-weight: bold; margin: 0.5rem 0;">+ {package["bonus"]} Bonus Credits!</div>' if package["bonus"] > 0 else ''}
            
            <div style="background: rgba(217,104,51,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <div style="font-size: 1.8rem; font-weight: bold; color: #d96833;">${package["price"]:.2f}</div>
                <p style="color: #7b756a; margin: 0; font-size: 0.9rem;">${price_per_credit:.2f} per credit</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Purchase {total_credits} Credits", key=f"credits_{package['credits']}"):
            PaymentUI.handle_credit_purchase(total_credits, package["price"])
    
    @staticmethod
    def handle_credit_purchase(credits: int, price: float):
        """Handle credit purchase"""
        st.session_state.selected_credits = credits
        st.session_state.selected_price = price
        st.session_state.show_credit_payment = True
        st.rerun()
    
    @staticmethod
    def render_payment_form():
        """Render payment form with Stripe integration"""
        if not st.session_state.get('show_payment_form') and not st.session_state.get('show_credit_payment'):
            return
        
        st.markdown("""
        <div style='margin: 2rem 0; text-align: center;'>
            <h3 style='color: #ece7e2;'>Complete Your Purchase</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("payment_form"):
            # Customer information
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email Address", placeholder="your@email.com")
            with col2:
                name = st.text_input("Full Name", placeholder="John Doe")
            
            # Payment method selection
            payment_method = st.radio(
                "Payment Method",
                ["Credit Card", "PayPal", "Apple Pay", "Google Pay"],
                horizontal=True
            )
            
            # Terms and conditions
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            # Submit button
            submit_button = st.form_submit_button("Complete Purchase", disabled=not agree_terms)
            
            if submit_button and email and name and agree_terms:
                PaymentUI.process_payment(email, name, payment_method)
    
    @staticmethod
    def process_payment(email: str, name: str, payment_method: str):
        """Process payment through Stripe"""
        try:
            if st.session_state.get('show_payment_form'):
                # Subscription payment
                tier = st.session_state.selected_tier
                billing_cycle = st.session_state.selected_billing
                
                checkout_url = payment_service.create_subscription_checkout(
                    customer_email=email,
                    tier=tier,
                    billing_cycle=billing_cycle,
                    success_url="https://your-domain.com/success",
                    cancel_url="https://your-domain.com/cancel"
                )
                
                PaymentUI.show_payment_redirect(checkout_url, "subscription")
            
            elif st.session_state.get('show_credit_payment'):
                # Credit purchase
                credits = st.session_state.selected_credits
                price = st.session_state.selected_price
                
                checkout_url = payment_service.create_credits_checkout(
                    customer_email=email,
                    credits_amount=credits,
                    price_per_credit=price / credits,
                    success_url="https://your-domain.com/success",
                    cancel_url="https://your-domain.com/cancel"
                )
                
                PaymentUI.show_payment_redirect(checkout_url, "credits")
        
        except Exception as e:
            st.error(f"Payment processing failed: {str(e)}")
    
    @staticmethod
    def show_payment_redirect(checkout_url: str, payment_type: str):
        """Show payment redirect with QR code and direct link"""
        st.success("Payment session created successfully!")
        
        # Generate QR code for mobile payments
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(checkout_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_b64 = base64.b64encode(qr_buffer.getvalue()).decode()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card" style="text-align: center;">
                <h4 style="color: #d96833;">Desktop Payment</h4>
                <p style="color: #7b756a;">Click the button below to proceed to secure checkout</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔒 Proceed to Secure Checkout", use_container_width=True):
                st.markdown(f"""
                <script>
                    window.open('{checkout_url}', '_blank');
                </script>
                """, unsafe_allow_html=True)
                st.info("Please complete your payment in the new window that opened.")
        
        with col2:
            st.markdown(f"""
            <div class="feature-card" style="text-align: center;">
                <h4 style="color: #d96833;">Mobile Payment</h4>
                <p style="color: #7b756a;">Scan with your phone camera</p>
                <img src="data:image/png;base64,{qr_b64}" style="max-width: 200px; border-radius: 10px;">
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_account_management():
        """Render account and subscription management"""
        if 'user_email' not in st.session_state:
            PaymentUI.render_login_form()
            return
        
        user_email = st.session_state.user_email
        user_info = payment_service.get_user_info(user_email)
        
        if not user_info:
            st.error("User information not found.")
            return
        
        st.markdown("""
        <div style='margin: 2rem 0; text-align: center;'>
            <h2 style='color: #ece7e2;'>Account Management</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Current subscription info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="feature-card">
                <h3 style="color: #d96833;">Current Plan</h3>
                <div style="font-size: 1.5rem; font-weight: bold; color: #ece7e2; margin: 1rem 0;">
                    {user_info['subscription_tier'].title()}
                </div>
                <p style="color: #7b756a;">Member since: {user_info['created_at'][:10]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="feature-card">
                <h3 style="color: #d96833;">Available Credits</h3>
                <div style="font-size: 3rem; font-weight: bold; color: #ece7e2; margin: 1rem 0;">
                    {user_info['credits']}
                </div>
                <p style="color: #7b756a;">videos remaining</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Account actions
        st.markdown("<h3 style='color: #ece7e2; margin: 2rem 0 1rem 0;'>Account Actions</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Upgrade Plan", use_container_width=True):
                st.session_state.show_pricing = True
                st.rerun()
        
        with col2:
            if st.button("💳 Buy Credits", use_container_width=True):
                st.session_state.show_credit_purchase = True
                st.rerun()
        
        with col3:
            if user_info['subscription_tier'] != 'free':
                if st.button("❌ Cancel Subscription", use_container_width=True):
                    PaymentUI.handle_subscription_cancellation(user_email)
        
        # Payment history
        PaymentUI.render_payment_history(user_email)
    
    @staticmethod
    def render_login_form():
        """Simple login form for account management"""
        st.markdown("""
        <div style='margin: 2rem 0; text-align: center;'>
            <h3 style='color: #ece7e2;'>Access Your Account</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email Address")
            
            if st.form_submit_button("Access Account"):
                if email and "@" in email:
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Please enter a valid email address.")
    
    @staticmethod
    def render_payment_history(user_email: str):
        """Render payment history table"""
        payments = payment_service.get_payment_history(user_email)
        
        if not payments:
            return
        
        st.markdown("<h3 style='color: #ece7e2; margin: 2rem 0 1rem 0;'>Payment History</h3>", unsafe_allow_html=True)
        
        # Convert to display format
        payment_data = []
        for payment in payments[:10]:  # Show last 10 payments
            payment_data.append({
                "Date": payment['created_at'][:10],
                "Type": payment['payment_type'].title(),
                "Amount": f"${payment['amount']:.2f}",
                "Status": payment['status'].title(),
                "Credits": payment['credits_purchased'] or "-"
            })
        
        if payment_data:
            st.dataframe(payment_data, use_container_width=True)
    
    @staticmethod
    def handle_subscription_cancellation(user_email: str):
        """Handle subscription cancellation"""
        if payment_service.cancel_subscription(user_email):
            st.success("Subscription canceled successfully. You can continue using your remaining credits.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to cancel subscription. Please contact support.")


# Usage examples for integration
def show_pricing_page():
    """Main pricing page"""
    PaymentUI.render_pricing_cards()
    PaymentUI.render_credit_purchase()
    PaymentUI.render_payment_form()


def show_account_page():
    """Account management page"""
    PaymentUI.render_account_management()