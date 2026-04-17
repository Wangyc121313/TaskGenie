import React from 'react';
import { ScrollView, Text, TouchableOpacity, View } from 'react-native';


class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App render failed:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.badge}>Startup Error</Text>
          <Text style={styles.title}>The app hit a render error.</Text>
          <Text style={styles.message}>
            {this.state.error?.message || 'Unknown render error'}
          </Text>
          <Text style={styles.hint}>
            Check Metro or Android logs after reloading. This screen prevents a silent white page.
          </Text>
          <TouchableOpacity style={styles.button} onPress={this.handleReset}>
            <Text style={styles.buttonText}>Try Render Again</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    );
  }
}


const styles = {
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 40,
  },
  badge: {
    alignSelf: 'flex-start',
    marginBottom: 14,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: '#FEE2E2',
    color: '#991B1B',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  title: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '800',
    marginBottom: 12,
  },
  message: {
    color: '#F8FAFC',
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 14,
  },
  hint: {
    color: '#94A3B8',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 24,
  },
  button: {
    alignSelf: 'flex-start',
    backgroundColor: '#6366F1',
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
};


export default AppErrorBoundary;
