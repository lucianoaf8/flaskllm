# api/v1/routes.py (additional endpoint)
examples_ns = api.namespace('examples', description='API usage examples')

@examples_ns.route('')
class Examples(Resource):
    @examples_ns.doc(security='apikey')
    @require_api_token
    def get(self):
        """Get examples of how to use the API"""
        return {
            'examples': [
                {
                    'name': 'Process email summary',
                    'description': 'Extract key information from an email',
                    'request': {
                        'method': 'POST',
                        'url': '/api/v1/webhook',
                        'headers': {
                            'Content-Type': 'application/json',
                            'X-API-Token': '[your-api-token]'
                        },
                        'body': {
                            'prompt': 'Please summarize this email: We need to schedule a meeting to discuss Q3 results.',
                            'source': 'email',
                            'type': 'summary'
                        }
                    },
                    'response': {
                        'summary': 'A meeting needs to be scheduled to discuss Q3 results.',
                        'processing_time': 1.25
                    }
                },
                # Add more examples here
            ]
        }
