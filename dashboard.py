import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import yfinance as yf

# Load data
symbols = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/nifty50_symbols.csv'))['Symbol'].tolist()
ta_data = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/nifty50_data_ta.csv'))
fa_data = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/nifty50_fundamentals.csv'))

# Clean fundamental data
fa_data = fa_data[fa_data['Symbol'] != 'NIFTY 50']  # Remove the NIFTY 50 row
fa_data = fa_data.dropna(subset=['Company'])  # Remove rows with missing company names

st.set_page_config(page_title="Nifty 50 Dashboard", layout="wide")
st.title("Nifty 50 Dashboard")

# Multi-select for comparison
selected_stocks = st.multiselect("Select stocks to compare", symbols, default=symbols[:2])

tab1, tab2 = st.tabs(["📊 Fundamental Analysis", "📰 Market News"])

# Function to fetch today's open and latest close for a list of symbols
@st.cache_data(ttl=3600)
def fetch_intraday_prices(symbols):
    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                today_open = hist['Open'][0]
                latest_close = hist['Close'][-1]
                data[symbol] = {
                    'open': today_open,
                    'close': latest_close,
                    'return': ((latest_close - today_open) / today_open) * 100
                }
            else:
                data[symbol] = {'open': None, 'close': None, 'return': None}
        except Exception:
            data[symbol] = {'open': None, 'close': None, 'return': None}
    return data

# Function to fetch market news
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_market_news():
    """Fetch market news from various sources"""
    news_data = []
    
    try:
        # Try to fetch news from a free API (using NewsAPI as example)
        # Note: You'll need to get a free API key from https://newsapi.org/
        api_key = "demo_key"  # Replace with your actual API key
        
        # Keywords for Indian market news
        keywords = ["Nifty 50", "Sensex", "BSE", "NSE", "Indian stock market", "Indian economy"]
        
        for keyword in keywords[:3]:  # Limit to avoid API rate limits
            try:
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'q': keyword,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 5,
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        for article in data['articles']:
                            news_data.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', ''),
                                'keyword': keyword
                            })
            except Exception as e:
                st.warning(f"Could not fetch news for '{keyword}': {str(e)}")
                continue
                
    except Exception as e:
        st.warning(f"News API not available: {str(e)}")
    
    # If no news from API, provide sample market news
    if not news_data:
        sample_news = [
            {
                'title': 'Nifty 50 reaches new all-time high',
                'description': 'The Nifty 50 index surged to a new record high, driven by strong corporate earnings and positive global cues.',
                'url': '#',
                'publishedAt': datetime.now().isoformat(),
                'source': 'Market Update',
                'keyword': 'Nifty 50'
            },
            {
                'title': 'RBI maintains repo rate at 6.5%',
                'description': 'The Reserve Bank of India kept the repo rate unchanged in its latest monetary policy meeting.',
                'url': '#',
                'publishedAt': (datetime.now() - timedelta(hours=2)).isoformat(),
                'source': 'Economic News',
                'keyword': 'Indian economy'
            },
            {
                'title': 'IT sector leads market gains',
                'description': 'Information technology stocks led the market rally with TCS and Infosys posting strong quarterly results.',
                'url': '#',
                'publishedAt': (datetime.now() - timedelta(hours=4)).isoformat(),
                'source': 'Sector Analysis',
                'keyword': 'Indian stock market'
            },
            {
                'title': 'FIIs continue buying spree',
                'description': 'Foreign Institutional Investors have been net buyers for the third consecutive week.',
                'url': '#',
                'publishedAt': (datetime.now() - timedelta(hours=6)).isoformat(),
                'source': 'Market Analysis',
                'keyword': 'BSE'
            },
            {
                'title': 'Banking stocks show resilience',
                'description': 'Banking sector stocks showed strong performance despite global banking concerns.',
                'url': '#',
                'publishedAt': (datetime.now() - timedelta(hours=8)).isoformat(),
                'source': 'Sector Update',
                'keyword': 'NSE'
            }
        ]
        news_data = sample_news
    
    return news_data

with tab1:
    # Filter and clean fundamental data
    fa_selected = fa_data[fa_data['Symbol'].isin(selected_stocks)].copy()
    
    if not fa_selected.empty:
        st.subheader("📊 Fundamental Analysis Dashboard")
        # Fetch intraday prices and returns for selected stocks
        price_data = fetch_intraday_prices(fa_selected['Symbol'].tolist())
        fa_selected['Today Open'] = fa_selected['Symbol'].map(lambda s: price_data[s]['open'])
        fa_selected['Current Close'] = fa_selected['Symbol'].map(lambda s: price_data[s]['close'])
        fa_selected['Return (%)'] = fa_selected['Symbol'].map(lambda s: price_data[s]['return'])
        # Clean numeric columns - replace inf values and handle missing data
        numeric_columns = fa_selected.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            fa_selected[col] = pd.to_numeric(fa_selected[col], errors='coerce')
            fa_selected[col] = fa_selected[col].replace([np.inf, -np.inf], np.nan)
        # --- SUMMARY SECTION: Best Performing Stock by Return ---
        st.markdown("""
        <div style='padding: 18px 0 10px 0; text-align: center;'>
            <span style='font-size: 2.2rem; font-weight: bold; color: #007bff;'>🏅 Best Performing Stock (Today)</span>
        </div>
        """, unsafe_allow_html=True)
        if 'Return (%)' in fa_selected.columns and fa_selected['Return (%)'].notna().any():
            best_idx = fa_selected['Return (%)'].idxmax()
            best_row = fa_selected.loc[best_idx]
            best_symbol = best_row['Symbol']
            best_company = best_row['Company']
            today_open = best_row['Today Open']
            current_close = best_row['Current Close']
            best_return = best_row['Return (%)']
            st.markdown(f"""
            <div style='display: flex; justify-content: center; align-items: center; gap: 30px; margin-bottom: 10px;'>
                <div style='background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%); border-radius: 16px; padding: 24px 36px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);'>
                    <span style='font-size: 1.5rem; font-weight: bold; color: #222;'>🏆 {best_company}</span><br>
                    <span style='font-size: 1.1rem; color: #555;'>({best_symbol})</span><br>
                    <span style='font-size: 1.15rem; color: #555;'>Open: {f'₹{today_open:,.2f}' if today_open else 'N/A'}</span><br>
                    <span style='font-size: 1.3rem; color: #28a745; font-weight: bold;'>
                        Close: {f'₹{current_close:,.2f}' if current_close else 'N/A'}
                    </span><br>
                    <span style='font-size: 1.2rem; color: #007bff; font-weight: bold;'>
                        Return: {f'{best_return:.2f}%' if best_return else 'N/A'}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        # --- KPI TABS ---
        fa_tab1, fa_tab2, fa_tab3, fa_tab4 = st.tabs(["📈 Key Metrics", "💰 Valuation", "📊 Financial Health", "🏭 Sector Analysis"])
        
        with fa_tab1:
            st.subheader("🎯 Key Performance Indicators")
            key_metrics = ['Market Cap (₹100 Cr)', 'P/E Ratio', 'EPS', 'ROE (%)', 'Profit Margin (%)', 'ROA (%)', 'Debt/Equity', 'Return (%)']
            available_key_metrics = [col for col in key_metrics if col in fa_selected.columns]
            if available_key_metrics:
                metric_cols = st.columns(len(available_key_metrics))
                for i, metric in enumerate(available_key_metrics):
                    with metric_cols[i]:
                        # Only proceed if there are non-NA values
                        if fa_selected[metric].notna().any():
                            if metric == 'Return (%)':
                                best_idx = fa_selected[metric].idxmax()
                            elif 'Market Cap' in metric or 'EPS' in metric or 'ROE' in metric or 'Profit Margin' in metric or 'ROA' in metric:
                                best_idx = fa_selected[metric].idxmax()
                            else:
                                best_idx = fa_selected[metric].idxmin()
                            best_row = fa_selected.loc[best_idx]
                            best_symbol = best_row['Symbol']
                            best_company = best_row['Company']
                            best_value = best_row[metric]
                            current_close = best_row['Current Close'] if 'Current Close' in best_row else None
                            # Color coding and status
                            if metric == 'Return (%)':
                                color = "#007bff"; status = "Top Gainer"
                            elif 'Market Cap' in metric:
                                if best_value > 500:
                                    color = "#28a745"; status = "Large Cap"
                                elif best_value > 200:
                                    color = "#ffc107"; status = "Mid Cap"
                                else:
                                    color = "#dc3545"; status = "Small Cap"
                            elif 'P/E Ratio' in metric:
                                if best_value < 15:
                                    color = "#28a745"; status = "Undervalued"
                                elif best_value < 25:
                                    color = "#ffc107"; status = "Fair Value"
                                else:
                                    color = "#dc3545"; status = "Overvalued"
                            elif 'ROE' in metric:
                                if best_value > 20:
                                    color = "#28a745"; status = "Excellent"
                                elif best_value > 10:
                                    color = "#ffc107"; status = "Good"
                                else:
                                    color = "#dc3545"; status = "Poor"
                            else:
                                color = "#007bff"; status = "Normal"
                            st.markdown(f"""
                            <div style="
                                border: 2px solid {color};
                                border-radius: 14px;
                                padding: 18px 10px 14px 10px;
                                text-align: center;
                                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                                margin-bottom: 10px;
                            ">
                                <div style='font-size: 1.2rem; font-weight: bold; color: #2c3e50; margin-bottom: 6px;'>{metric}</div>
                                <div style='font-size: 2.1rem; font-weight: bold; color: {color}; margin: 8px 0 2px 0;'>
                                    {best_value:.2f}
                                </div>
                                <div style='font-size: 1.1rem; color: #222; font-weight: 600; margin-bottom: 2px;'>
                                    <span style='color: #007bff;'>🏢 {best_company}</span>
                                </div>
                                <div style='font-size: 1.05rem; color: #555; margin-bottom: 2px;'>({best_symbol})</div>
                                <div style='font-size: 1.15rem; color: #28a745; font-weight: bold; margin-bottom: 2px;'>
                                    {f'₹{current_close:,.2f}' if current_close else 'Price N/A'}
                                </div>
                                <div style="
                                    background-color: {color};
                                    color: white;
                                    padding: 4px 8px;
                                    border-radius: 12px;
                                    font-size: 13px;
                                    font-weight: bold;
                                    margin-top: 8px;
                                    display: inline-block;
                                ">{status}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='color:#dc3545; font-weight:bold; text-align:center; margin:10px 0;'>No data for {metric}</div>", unsafe_allow_html=True)
                
                # Add comparison chart
                st.subheader("📊 Metric Comparison Chart")
                if len(available_key_metrics) > 1:
                    # Create comparison chart
                    fig = go.Figure()
                    
                    for metric in available_key_metrics[:3]:  # Limit to 3 metrics for clarity
                        values = fa_selected[metric].values
                        companies = fa_selected['Company'].values
                        
                        fig.add_trace(go.Bar(
                            name=metric,
                            x=companies,
                            y=values,
                            text=[f'{v:.2f}' for v in values],
                            textposition='auto',
                        ))
                    
                    fig.update_layout(
                        title=f"Comparison of Key Metrics",
                        xaxis_title="Companies",
                        yaxis_title="Values",
                        barmode='group',
                        height=500,
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with fa_tab2:
            st.subheader("💰 Valuation Analysis")
            
            # Valuation metrics
            valuation_metrics = ['P/E Ratio', 'Forward P/E', 'PEG Ratio', 'P/B Ratio', 'Dividend Yield (%)']
            available_valuation = [col for col in valuation_metrics if col in fa_selected.columns]
            
            if available_valuation:
                # Create valuation table with enhanced styling
                valuation_data = fa_selected[['Company'] + available_valuation].set_index('Company')
                
                def style_valuation(val, col):
                    if pd.isna(val):
                        return 'background-color: #f8f9fa; color: #6c757d; font-style: italic;'
                    
                    if isinstance(val, (int, float)):
                        if 'P/E Ratio' in col or 'Forward P/E' in col:
                            if val < 15:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val < 25:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                        elif 'PEG Ratio' in col:
                            if val < 1:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val < 2:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                        elif 'P/B Ratio' in col:
                            if val < 1:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val < 3:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                        elif 'Dividend Yield' in col:
                            if val > 5:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val > 2:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                    return ''
                
                styled_valuation = valuation_data.style.apply(
                    lambda x: [style_valuation(val, col) for val, col in zip(x, x.index)], axis=1
                ).set_properties(**{
                    'border': '1px solid #dee2e6',
                    'border-radius': '8px',
                    'padding': '12px',
                    'text-align': 'center',
                    'font-family': 'Arial, sans-serif',
                    'font-size': '14px'
                }).set_table_styles([
                    {'selector': 'th', 'props': [
                        ('background-color', '#343a40'),
                        ('color', 'white'),
                        ('font-weight', 'bold'),
                        ('text-align', 'center'),
                        ('padding', '15px'),
                        ('border', '1px solid #dee2e6')
                    ]},
                    {'selector': 'td', 'props': [
                        ('border', '1px solid #dee2e6'),
                        ('padding', '12px'),
                        ('text-align', 'center')
                    ]}
                ]).format('{:.2f}')
                
                st.write(styled_valuation)
                
                # Valuation insights
                st.subheader("💡 Valuation Insights")
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    if 'P/E Ratio' in available_valuation:
                        min_pe = valuation_data['P/E Ratio'].min()
                        min_pe_company = valuation_data['P/E Ratio'].idxmin()
                        st.metric(
                            label="💰 Most Undervalued (P/E)",
                            value=f"{min_pe:.2f}",
                            delta=f"{min_pe_company}"
                        )
                
                with insight_col2:
                    if 'PEG Ratio' in available_valuation:
                        min_peg = valuation_data['PEG Ratio'].min()
                        min_peg_company = valuation_data['PEG Ratio'].idxmin()
                        st.metric(
                            label="📈 Best Growth Value (PEG)",
                            value=f"{min_peg:.2f}",
                            delta=f"{min_peg_company}"
                        )
                
                with insight_col3:
                    if 'Dividend Yield (%)' in available_valuation:
                        max_div = valuation_data['Dividend Yield (%)'].max()
                        max_div_company = valuation_data['Dividend Yield (%)'].idxmax()
                        st.metric(
                            label="💵 Highest Dividend Yield",
                            value=f"{max_div:.2f}%",
                            delta=f"{max_div_company}"
                        )
        
        with fa_tab3:
            st.subheader("📊 Financial Health Analysis")
            
            # Financial health metrics
            health_metrics = ['ROE (%)', 'ROA (%)', 'Profit Margin (%)', 'Operating Margin (%)', 'Debt/Equity', 'Current Ratio', 'Quick Ratio']
            available_health = [col for col in health_metrics if col in fa_selected.columns]
            
            if available_health:
                # Create financial health radar chart
                if len(available_health) >= 3:
                    fig = go.Figure()
                    
                    for idx, company in enumerate(fa_selected['Company']):
                        values = []
                        for metric in available_health[:5]:  # Limit to 5 metrics for radar chart
                            val = fa_selected[fa_selected['Company'] == company][metric].iloc[0]
                            if pd.notna(val):
                                values.append(val)
                            else:
                                values.append(0)
                        
                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=available_health[:5],
                            fill='toself',
                            name=company,
                            line_color=f'rgb({50 + idx*50}, {100 + idx*30}, {150 + idx*20})'
                        ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, max([fa_selected[col].max() for col in available_health[:5] if fa_selected[col].max() > 0])]
                            )),
                        showlegend=True,
                        title="Financial Health Radar Chart",
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Financial health table
                health_data = fa_selected[['Company'] + available_health].set_index('Company')
                
                def style_health(val, col):
                    if pd.isna(val):
                        return 'background-color: #f8f9fa; color: #6c757d; font-style: italic;'
                    
                    if isinstance(val, (int, float)):
                        if 'ROE' in col or 'ROA' in col or 'Profit Margin' in col or 'Operating Margin' in col:
                            if val > 20:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val > 10:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                        elif 'Debt/Equity' in col:
                            if val < 0.5:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val < 1:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                        elif 'Current Ratio' in col or 'Quick Ratio' in col:
                            if val > 2:
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif val > 1:
                                return 'background-color: #fff3cd; color: #856404;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24;'
                    return ''
                
                styled_health = health_data.style.apply(
                    lambda x: [style_health(val, col) for val, col in zip(x, x.index)], axis=1
                ).set_properties(**{
                    'border': '1px solid #dee2e6',
                    'border-radius': '8px',
                    'padding': '12px',
                    'text-align': 'center',
                    'font-family': 'Arial, sans-serif',
                    'font-size': '14px'
                }).set_table_styles([
                    {'selector': 'th', 'props': [
                        ('background-color', '#343a40'),
                        ('color', 'white'),
                        ('font-weight', 'bold'),
                        ('text-align', 'center'),
                        ('padding', '15px'),
                        ('border', '1px solid #dee2e6')
                    ]},
                    {'selector': 'td', 'props': [
                        ('border', '1px solid #dee2e6'),
                        ('padding', '12px'),
                        ('text-align', 'center')
                    ]}
                ]).format('{:.2f}')
                
                st.write(styled_health)
        
        with fa_tab4:
            st.subheader("🏭 Sector Analysis")
            
            if 'Sector' in fa_selected.columns:
                # Sector distribution
                sector_counts = fa_selected['Sector'].value_counts()
                
                # Create sector pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=sector_counts.index,
                    values=sector_counts.values,
                    hole=0.3,
                    marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
                )])
                
                fig.update_layout(
                    title="Sector Distribution",
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Sector performance comparison
                st.subheader("📈 Sector Performance Comparison")
                
                # Calculate average metrics by sector
                sector_metrics = ['Market Cap (₹100 Cr)', 'P/E Ratio', 'ROE (%)', 'Profit Margin (%)']
                available_sector_metrics = [col for col in sector_metrics if col in fa_selected.columns]
                
                if available_sector_metrics:
                    sector_avg = fa_selected.groupby('Sector')[available_sector_metrics].mean()
                    
                    # Create sector comparison chart
                    fig = go.Figure()
                    
                    for metric in available_sector_metrics:
                        fig.add_trace(go.Bar(
                            name=metric,
                            x=sector_avg.index,
                            y=sector_avg[metric],
                            text=[f'{v:.2f}' for v in sector_avg[metric]],
                            textposition='auto',
                        ))
                    
                    fig.update_layout(
                        title="Average Metrics by Sector",
                        xaxis_title="Sectors",
                        yaxis_title="Average Values",
                        barmode='group',
                        height=500,
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Sector insights
                    st.subheader("💡 Sector Insights")
                    
                    # Find best performing sector for each metric
                    for metric in available_sector_metrics:
                        if sector_avg[metric].notna().any():
                            if 'Market Cap' in metric or 'ROE' in metric or 'Profit Margin' in metric:
                                best_sector = sector_avg[metric].idxmax()
                                best_value = sector_avg[metric].max()
                            else:  # For P/E, lower is better
                                best_sector = sector_avg[metric].idxmin()
                                best_value = sector_avg[metric].min()
                            st.info(f"🏆 **{metric}**: {best_sector} leads with {best_value:.2f}")
                        else:
                            st.info(f"No data for {metric}")
        
        # Original comprehensive table (moved to bottom)
        st.subheader("📋 Comprehensive Fundamental Data")
        
        # Dynamic column selection
        all_columns = [col for col in fa_selected.columns if col not in ['Symbol', 'Company']]
        default_cols = ['Market Cap (₹100 Cr)', 'P/E Ratio', 'EPS', 'ROE (%)', 'Profit Margin (%)', 'Sector']
        
        # Filter available columns
        available_cols = [col for col in default_cols if col in fa_selected.columns]
        selected_cols = st.multiselect(
            "🎯 Select metrics to compare", 
            ['Company'] + all_columns, 
            default=['Company'] + available_cols
        )
        
        if selected_cols:
            # Only set index if 'Company' is in the selected columns
            if 'Company' in selected_cols:
                fa_display = fa_selected[selected_cols].set_index('Company')
            else:
                fa_display = fa_selected[selected_cols]
                st.warning("'Company' column is not selected. Table will not be indexed by company name.")
            
            # Format numeric columns for better display with colors
            numeric_cols = fa_display.select_dtypes(include=[np.number]).columns
            formatted_display = fa_display.copy()
            
            # Create a styled DataFrame with colors
            def style_fundamental_data(val, col):
                if pd.isna(val):
                    return 'background-color: #f8f9fa; color: #6c757d; font-style: italic;'
                
                if isinstance(val, (int, float)):
                    # Color coding based on column type
                    if 'Market Cap' in col:
                        if val > 500:
                            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                        elif val > 200:
                            return 'background-color: #fff3cd; color: #856404;'
                        else:
                            return 'background-color: #f8d7da; color: #721c24;'
                    
                    elif 'P/E Ratio' in col:
                        if val < 15:
                            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                        elif val < 25:
                            return 'background-color: #fff3cd; color: #856404;'
                        else:
                            return 'background-color: #f8d7da; color: #721c24;'
                    
                    elif 'ROE' in col:
                        if val > 20:
                            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                        elif val > 10:
                            return 'background-color: #fff3cd; color: #856404;'
                        else:
                            return 'background-color: #f8d7da; color: #721c24;'
                    
                    elif 'Profit Margin' in col:
                        if val > 15:
                            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                        elif val > 5:
                            return 'background-color: #fff3cd; color: #856404;'
                        else:
                            return 'background-color: #f8d7da; color: #721c24;'
                    
                    elif 'EPS' in col:
                        if val > 50:
                            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                        elif val > 20:
                            return 'background-color: #fff3cd; color: #856404;'
                        else:
                            return 'background-color: #f8d7da; color: #721c24;'
                    
                    else:
                        return 'background-color: #e9ecef; color: #495057;'
                
                return ''
            
            # Apply styling
            styled_df = fa_display.style.apply(lambda x: [style_fundamental_data(val, col) for val, col in zip(x, x.index)], axis=1)
            
            # Format values with proper formatting
            for col in numeric_cols:
                if 'Market Cap' in col:
                    styled_df = styled_df.format({col: '{:,.2f}'})
                elif 'Ratio' in col or 'Yield' in col or 'Margin' in col or 'ROE' in col or 'ROA' in col:
                    styled_df = styled_df.format({col: '{:.2f}'})
                elif 'EPS' in col:
                    styled_df = styled_df.format({col: '{:.2f}'})
                else:
                    styled_df = styled_df.format({col: '{:.2f}'})
            
            # Add hover effects and better table styling
            styled_df = styled_df.set_properties(**{
                'border': '1px solid #dee2e6',
                'border-radius': '8px',
                'padding': '12px',
                'text-align': 'center',
                'font-family': 'Arial, sans-serif',
                'font-size': '14px'
            }).set_table_styles([
                {'selector': 'th', 'props': [
                    ('background-color', '#343a40'),
                    ('color', 'white'),
                    ('font-weight', 'bold'),
                    ('text-align', 'center'),
                    ('padding', '15px'),
                    ('border', '1px solid #dee2e6'),
                    ('border-radius', '8px 8px 0 0')
                ]},
                {'selector': 'td', 'props': [
                    ('border', '1px solid #dee2e6'),
                    ('padding', '12px'),
                    ('text-align', 'center')
                ]},
                {'selector': 'tr:nth-child(even)', 'props': [
                    ('background-color', '#f8f9fa')
                ]},
                {'selector': 'tr:hover', 'props': [
                    ('background-color', '#e3f2fd'),
                    ('transform', 'scale(1.02)'),
                    ('transition', 'all 0.3s ease')
                ]}
            ])
            
            # Display the styled table
            st.write(styled_df)
            
            # Add color legend
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>🟢 Excellent</strong><br>
                    Above average performance
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>🟡 Good</strong><br>
                    Average performance
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>🔴 Needs Attention</strong><br>
                    Below average performance
                </div>
                """, unsafe_allow_html=True)
            
            # Add insights
            st.subheader("💡 Key Insights")
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                if 'Market Cap (₹100 Cr)' in numeric_cols and fa_display['Market Cap (₹100 Cr)'].notna().any():
                    max_market_cap = fa_display['Market Cap (₹100 Cr)'].max()
                    max_company = fa_display['Market Cap (₹100 Cr)'].idxmax()
                    st.metric(
                        label="🏆 Highest Market Cap",
                        value=f"₹{max_market_cap:,.2f} Cr",
                        delta=f"{max_company}"
                    )
                else:
                    st.info("No data for Market Cap")
            
            with insights_col2:
                if 'P/E Ratio' in numeric_cols:
                    min_pe = fa_display['P/E Ratio'].min()
                    min_pe_company = fa_display['P/E Ratio'].idxmin()
                    st.metric(
                        label="💰 Lowest P/E Ratio",
                        value=f"{min_pe:.2f}",
                        delta=f"{min_pe_company}"
                    )
        else:
            st.info("📋 Please select at least one metric to display.")
    else:
        st.warning("⚠️ No fundamental data available for selected stocks.")

with tab2:
    st.subheader("📰 Latest Market News & Updates")
    
    # Add refresh button
    if st.button("🔄 Refresh News"):
        st.cache_data.clear()
        st.rerun()
    
    # Fetch news
    news_data = fetch_market_news()
    
    if news_data:
        # Display news in a beautiful format
        for i, news in enumerate(news_data):
            # Parse publication date
            try:
                pub_date = datetime.fromisoformat(news['publishedAt'].replace('Z', '+00:00'))
                time_ago = datetime.now(pub_date.tzinfo) - pub_date
                if time_ago.days > 0:
                    time_str = f"{time_ago.days} days ago"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds // 3600} hours ago"
                else:
                    time_str = f"{time_ago.seconds // 60} minutes ago"
            except:
                time_str = "Recently"
            
            # Create news card
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    transition: transform 0.2s ease;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <h3 style="margin: 0; color: #2c3e50; font-size: 18px;">{news['title']}</h3>
                        <span style="
                            background-color: #007bff;
                            color: white;
                            padding: 4px 8px;
                            border-radius: 12px;
                            font-size: 12px;
                            font-weight: bold;
                        ">{news['keyword']}</span>
                    </div>
                    <p style="color: #6c757d; margin: 10px 0; line-height: 1.6;">{news['description']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                        <div style="display: flex; gap: 15px; align-items: center;">
                            <span style="color: #28a745; font-weight: bold;">📰 {news['source']}</span>
                            <span style="color: #6c757d; font-size: 12px;">⏰ {time_str}</span>
                        </div>
                        <a href="{news['url']}" target="_blank" style="
                            background-color: #007bff;
                            color: white;
                            padding: 8px 16px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            transition: background-color 0.2s ease;
                        ">Read More</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Add market sentiment indicator
        st.subheader("📊 Market Sentiment")
        sentiment_col1, sentiment_col2, sentiment_col3 = st.columns(3)
        
        with sentiment_col1:
            st.metric(
                label="📈 Bullish News",
                value=len([n for n in news_data if any(word in n['title'].lower() for word in ['surge', 'gain', 'rise', 'high', 'positive'])]),
                delta="Positive"
            )
        
        with sentiment_col2:
            st.metric(
                label="📉 Bearish News",
                value=len([n for n in news_data if any(word in n['title'].lower() for word in ['fall', 'drop', 'decline', 'low', 'negative'])]),
                delta="Negative"
            )
        
        with sentiment_col3:
            st.metric(
                label="📊 Neutral News",
                value=len([n for n in news_data if not any(word in n['title'].lower() for word in ['surge', 'gain', 'rise', 'high', 'positive', 'fall', 'drop', 'decline', 'low', 'negative'])]),
                delta="Neutral"
            )
        
        # Add news categories
        st.subheader("🏷️ News Categories")
        categories = {}
        for news in news_data:
            keyword = news['keyword']
            if keyword not in categories:
                categories[keyword] = 0
            categories[keyword] += 1
        
        # Display category distribution
        category_cols = st.columns(len(categories))
        for i, (category, count) in enumerate(categories.items()):
            with category_cols[i]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #007bff, #0056b3);
                    color: white;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,123,255,0.3);
                ">
                    <h4 style="margin: 0 0 10px 0;">{category}</h4>
                    <div style="font-size: 24px; font-weight: bold;">{count}</div>
                    <div style="font-size: 12px;">articles</div>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        st.warning("⚠️ Unable to fetch news at the moment. Please try again later.")

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    .stTabs [data-baseweb="tab"] { font-size: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
) 