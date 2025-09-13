"""
TalkingPhoto AI MVP - Export Service
Platform-specific export instructions and workflow templates
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
import structlog

from models.video import VideoGeneration

logger = structlog.get_logger()


class ExportService:
    """
    Service for generating platform-specific export instructions and workflow templates
    """
    
    def __init__(self):
        self.platform_specs = {
            'instagram': {
                'aspect_ratios': {
                    'feed': '1:1',
                    'story': '9:16',
                    'reel': '9:16'
                },
                'video_specs': {
                    'max_duration': 60,
                    'resolution': '1080x1080',
                    'format': 'MP4',
                    'bitrate': '3500k',
                    'frame_rate': 30
                },
                'requirements': {
                    'file_size_limit': '100MB',
                    'audio_format': 'AAC',
                    'color_space': 'sRGB'
                }
            },
            'youtube': {
                'aspect_ratios': {
                    'standard': '16:9',
                    'shorts': '9:16'
                },
                'video_specs': {
                    'max_duration': 'unlimited',
                    'resolution': '1920x1080',
                    'format': 'MP4',
                    'bitrate': '8000k',
                    'frame_rate': 60
                },
                'requirements': {
                    'file_size_limit': '256GB',
                    'audio_format': 'AAC',
                    'color_space': 'sRGB'
                }
            },
            'linkedin': {
                'aspect_ratios': {
                    'feed': '16:9',
                    'story': '9:16'
                },
                'video_specs': {
                    'max_duration': 600,
                    'resolution': '1920x1080',
                    'format': 'MP4',
                    'bitrate': '5000k',
                    'frame_rate': 30
                },
                'requirements': {
                    'file_size_limit': '5GB',
                    'audio_format': 'AAC',
                    'color_space': 'sRGB'
                }
            },
            'tiktok': {
                'aspect_ratios': {
                    'standard': '9:16'
                },
                'video_specs': {
                    'max_duration': 180,
                    'resolution': '1080x1920',
                    'format': 'MP4',
                    'bitrate': '3000k',
                    'frame_rate': 30
                },
                'requirements': {
                    'file_size_limit': '287MB',
                    'audio_format': 'AAC',
                    'color_space': 'sRGB'
                }
            }
        }
        
        self.workflow_templates = {
            'product_demo': {
                'title': 'Product Demonstration',
                'description': 'Showcase product features with professional talking head explanation',
                'steps': [
                    'Create compelling opening hook',
                    'Demonstrate key features',
                    'Address common objections',
                    'Include clear call-to-action',
                    'Add captions for accessibility'
                ],
                'estimated_time': '2-3 hours',
                'tools_needed': ['Video editor', 'Captions tool', 'Brand assets']
            },
            'avatar_presentation': {
                'title': 'Avatar Presentation',
                'description': 'Professional presentation using AI-generated talking avatar',
                'steps': [
                    'Script professional presentation',
                    'Add brand elements and logos',
                    'Include engaging visual aids',
                    'Optimize for platform requirements',
                    'Test across different devices'
                ],
                'estimated_time': '1-2 hours',
                'tools_needed': ['Brand assets', 'Presentation slides', 'Logo files']
            },
            'lifestyle_content': {
                'title': 'Lifestyle Content',
                'description': 'Authentic lifestyle content with personal touch',
                'steps': [
                    'Create authentic personal message',
                    'Add lifestyle context',
                    'Include trending hashtags',
                    'Optimize posting time',
                    'Engage with comments'
                ],
                'estimated_time': '30 minutes',
                'tools_needed': ['Hashtag research', 'Analytics tools']
            },
            'testimonial': {
                'title': 'Customer Testimonial',
                'description': 'Professional testimonial format with credibility indicators',
                'steps': [
                    'Highlight customer credentials',
                    'Focus on specific results',
                    'Add supporting evidence',
                    'Include contact information',
                    'Add trust indicators'
                ],
                'estimated_time': '1 hour',
                'tools_needed': ['Customer photos', 'Result screenshots', 'Brand assets']
            }
        }
    
    def generate_instructions(self, video_generation: VideoGeneration, platform: str, 
                            workflow_type: str, additional_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive export instructions for specific platform and workflow
        """
        try:
            if platform not in self.platform_specs:
                return {'success': False, 'error': f'Platform {platform} not supported'}
            
            if workflow_type not in self.workflow_templates:
                return {'success': False, 'error': f'Workflow type {workflow_type} not supported'}
            
            platform_spec = self.platform_specs[platform]
            workflow = self.workflow_templates[workflow_type]
            
            # Generate platform-specific instructions
            instructions = {
                'platform': platform,
                'workflow_type': workflow_type,
                'video_info': {
                    'duration': f"{video_generation.duration_seconds} seconds",
                    'aspect_ratio': video_generation.aspect_ratio.value,
                    'quality': video_generation.video_quality.value,
                    'resolution': video_generation.video_resolution
                },
                'platform_requirements': platform_spec,
                'workflow_template': workflow,
                'step_by_step_guide': self._generate_step_by_step_guide(
                    platform, workflow_type, video_generation, additional_options or {}
                ),
                'optimization_tips': self._generate_optimization_tips(platform, workflow_type),
                'cost_breakdown': self._calculate_implementation_costs(platform, workflow_type),
                'success_metrics': self._define_success_metrics(platform, workflow_type),
                'troubleshooting': self._generate_troubleshooting_guide(platform)
            }
            
            return {'success': True, 'data': instructions}
            
        except Exception as e:
            logger.error("Instructions generation failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _generate_step_by_step_guide(self, platform: str, workflow_type: str, 
                                   video_generation: VideoGeneration, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate detailed step-by-step implementation guide
        """
        base_steps = [
            {
                'step': 1,
                'title': 'Download Your Generated Video',
                'description': 'Download the high-quality talking video from your dashboard',
                'actions': [
                    'Click the download button in your TalkingPhoto dashboard',
                    'Save the video file to your computer',
                    'Verify the video quality and duration'
                ],
                'estimated_time': '2 minutes',
                'required': True
            },
            {
                'step': 2,
                'title': 'Prepare Video for Platform',
                'description': f'Optimize video for {platform} requirements',
                'actions': self._get_platform_prep_actions(platform, video_generation),
                'estimated_time': '5-10 minutes',
                'required': True
            }
        ]
        
        # Add workflow-specific steps
        workflow_steps = self._get_workflow_specific_steps(workflow_type, platform)
        
        # Add platform-specific final steps
        final_steps = self._get_platform_final_steps(platform)
        
        # Combine all steps
        all_steps = base_steps + workflow_steps + final_steps
        
        # Number steps sequentially
        for i, step in enumerate(all_steps, 1):
            step['step'] = i
        
        return all_steps
    
    def _get_platform_prep_actions(self, platform: str, video_generation: VideoGeneration) -> List[str]:
        """
        Get platform-specific preparation actions
        """
        spec = self.platform_specs[platform]
        actions = []
        
        # Check aspect ratio compatibility
        video_ratio = video_generation.aspect_ratio.value
        platform_ratios = list(spec['aspect_ratios'].values())
        
        if video_ratio not in platform_ratios:
            actions.append(f"Crop or resize video to {platform_ratios[0]} aspect ratio using video editor")
        
        # Check duration
        max_duration = spec['video_specs'].get('max_duration')
        if isinstance(max_duration, int) and video_generation.duration_seconds > max_duration:
            actions.append(f"Trim video to {max_duration} seconds maximum")
        
        actions.extend([
            f"Ensure video resolution is {spec['video_specs']['resolution']}",
            f"Export in {spec['video_specs']['format']} format",
            f"Set bitrate to {spec['video_specs']['bitrate']}",
            "Add captions if required by platform"
        ])
        
        return actions
    
    def _get_workflow_specific_steps(self, workflow_type: str, platform: str) -> List[Dict[str, Any]]:
        """
        Get workflow-specific implementation steps
        """
        workflow_steps = {
            'product_demo': [
                {
                    'title': 'Add Product Information',
                    'description': 'Include product details and pricing',
                    'actions': [
                        'Add product name and key features as text overlay',
                        'Include pricing information if applicable',
                        'Add your website or contact information',
                        'Include product images or screenshots'
                    ],
                    'estimated_time': '10-15 minutes'
                },
                {
                    'title': 'Create Call-to-Action',
                    'description': 'Add compelling CTA to drive conversions',
                    'actions': [
                        'Add clear call-to-action text',
                        'Include link in bio or description',
                        'Use action-oriented language',
                        'Add urgency if appropriate'
                    ],
                    'estimated_time': '5 minutes'
                }
            ],
            'avatar_presentation': [
                {
                    'title': 'Add Professional Elements',
                    'description': 'Enhance with business branding',
                    'actions': [
                        'Add company logo as watermark',
                        'Include professional title/credentials',
                        'Add slide overlays if presenting data',
                        'Include contact information'
                    ],
                    'estimated_time': '15-20 minutes'
                }
            ],
            'lifestyle_content': [
                {
                    'title': 'Add Personal Touch',
                    'description': 'Make content authentic and relatable',
                    'actions': [
                        'Add casual, authentic captions',
                        'Include personal hashtags',
                        'Tag relevant locations',
                        'Add music that matches mood'
                    ],
                    'estimated_time': '10 minutes'
                }
            ],
            'testimonial': [
                {
                    'title': 'Add Credibility Elements',
                    'description': 'Enhance testimonial credibility',
                    'actions': [
                        'Add customer name and title',
                        'Include company/business logo',
                        'Add before/after results if applicable',
                        'Include date of testimonial'
                    ],
                    'estimated_time': '10-15 minutes'
                }
            ]
        }
        
        return workflow_steps.get(workflow_type, [])
    
    def _get_platform_final_steps(self, platform: str) -> List[Dict[str, Any]]:
        """
        Get platform-specific final steps
        """
        final_steps = {
            'instagram': [
                {
                    'title': 'Upload to Instagram',
                    'description': 'Post your video with optimal settings',
                    'actions': [
                        'Open Instagram app or Creator Studio',
                        'Select your optimized video file',
                        'Write engaging caption with relevant hashtags',
                        'Tag relevant accounts if appropriate',
                        'Choose optimal posting time',
                        'Monitor engagement and respond to comments'
                    ],
                    'estimated_time': '10 minutes'
                }
            ],
            'youtube': [
                {
                    'title': 'Upload to YouTube',
                    'description': 'Publish with SEO optimization',
                    'actions': [
                        'Go to YouTube Studio',
                        'Upload your video file',
                        'Add SEO-optimized title and description',
                        'Add relevant tags',
                        'Create custom thumbnail',
                        'Set appropriate category and visibility'
                    ],
                    'estimated_time': '15-20 minutes'
                }
            ],
            'linkedin': [
                {
                    'title': 'Post on LinkedIn',
                    'description': 'Share with professional network',
                    'actions': [
                        'Go to LinkedIn and create new post',
                        'Upload your video file',
                        'Write professional caption',
                        'Add relevant hashtags',
                        'Tag relevant connections',
                        'Share to relevant groups if appropriate'
                    ],
                    'estimated_time': '10 minutes'
                }
            ],
            'tiktok': [
                {
                    'title': 'Post on TikTok',
                    'description': 'Share with trending optimization',
                    'actions': [
                        'Open TikTok app',
                        'Upload your video',
                        'Add trending hashtags',
                        'Use relevant sounds if applicable',
                        'Add captions for accessibility',
                        'Post at optimal times'
                    ],
                    'estimated_time': '8 minutes'
                }
            ]
        }
        
        return final_steps.get(platform, [])
    
    def _generate_optimization_tips(self, platform: str, workflow_type: str) -> List[str]:
        """
        Generate platform and workflow-specific optimization tips
        """
        general_tips = [
            "Post during peak engagement hours for your audience",
            "Use relevant hashtags but don't overdo it",
            "Engage with comments within the first hour",
            "Cross-promote on other social platforms"
        ]
        
        platform_tips = {
            'instagram': [
                "Use Instagram Stories to promote your post",
                "Include a clear call-to-action in your caption",
                "Use location tags to increase discoverability",
                "Create engaging thumbnail for video posts"
            ],
            'youtube': [
                "Create eye-catching custom thumbnails",
                "Use YouTube Shorts for maximum reach",
                "Add end screens to promote other videos",
                "Enable captions for better accessibility"
            ],
            'linkedin': [
                "Write longer, value-driven captions",
                "Share industry insights in your post",
                "Engage with other professionals' content",
                "Post during business hours for B2B content"
            ],
            'tiktok': [
                "Hook viewers in the first 3 seconds",
                "Use trending sounds and hashtags",
                "Keep videos short and engaging",
                "Reply to comments with video responses"
            ]
        }
        
        return general_tips + platform_tips.get(platform, [])
    
    def _calculate_implementation_costs(self, platform: str, workflow_type: str) -> Dict[str, Any]:
        """
        Calculate estimated costs for workflow implementation
        """
        base_costs = {
            'time_investment': '1-3 hours',
            'tools_required': 'Free to $50/month',
            'additional_services': 'Optional'
        }
        
        detailed_costs = {
            'video_editing_software': {
                'free_options': ['DaVinci Resolve', 'OpenShot', 'iMovie'],
                'paid_options': ['Adobe Premiere Pro ($20/month)', 'Final Cut Pro ($299 one-time)']
            },
            'graphics_tools': {
                'free_options': ['Canva (limited)', 'GIMP'],
                'paid_options': ['Canva Pro ($12/month)', 'Adobe Creative Suite ($52/month)']
            },
            'scheduling_tools': {
                'free_options': ['Native platform scheduling'],
                'paid_options': ['Hootsuite ($49/month)', 'Buffer ($15/month)']
            }
        }
        
        return {
            'overview': base_costs,
            'detailed_breakdown': detailed_costs,
            'roi_estimate': 'Typically see 3-5x ROI within first month',
            'cost_optimization_tips': [
                'Start with free tools and upgrade as needed',
                'Batch create content to save time',
                'Repurpose content across multiple platforms',
                'Use templates to speed up production'
            ]
        }
    
    def _define_success_metrics(self, platform: str, workflow_type: str) -> Dict[str, Any]:
        """
        Define success metrics for tracking performance
        """
        general_metrics = {
            'engagement_rate': 'Aim for 3-5% minimum',
            'view_completion_rate': 'Target 60%+ for short videos',
            'click_through_rate': 'Aim for 2-3% for CTA links',
            'conversion_rate': 'Track based on your goals'
        }
        
        platform_metrics = {
            'instagram': {
                'likes_per_view': '8-12%',
                'comments_per_view': '0.5-1%',
                'shares_per_view': '0.2-0.5%',
                'story_completion_rate': '70%+'
            },
            'youtube': {
                'watch_time': 'Maximize average view duration',
                'subscriber_conversion': '1-3% of viewers',
                'click_through_rate': '2-10% on thumbnails',
                'retention_rate': '50%+ at 30 seconds'
            },
            'linkedin': {
                'professional_engagement': 'Comments from industry peers',
                'connection_requests': 'Increase in relevant connections',
                'profile_views': '50-100% increase post-video',
                'lead_generation': 'Track inquiries and messages'
            },
            'tiktok': {
                'completion_rate': '90%+ for under 15 seconds',
                'shares': '5-10% of total views',
                'duets_and_responses': 'Track user-generated content',
                'follower_growth': '1-5% per viral video'
            }
        }
        
        return {
            'general_metrics': general_metrics,
            'platform_specific': platform_metrics.get(platform, {}),
            'tracking_tools': [
                'Platform native analytics',
                'Google Analytics (for website traffic)',
                'UTM parameters for tracking',
                'Social listening tools'
            ]
        }
    
    def _generate_troubleshooting_guide(self, platform: str) -> List[Dict[str, str]]:
        """
        Generate common troubleshooting solutions
        """
        common_issues = [
            {
                'problem': 'Video quality looks poor after upload',
                'solution': 'Re-export at higher bitrate, check platform compression settings, upload during off-peak hours'
            },
            {
                'problem': 'Audio sync issues',
                'solution': 'Re-render video with matching audio sample rate, check for variable frame rate issues'
            },
            {
                'problem': 'Low engagement rates',
                'solution': 'Review posting times, improve thumbnail/preview, engage more with your audience, use trending hashtags'
            },
            {
                'problem': 'Video gets rejected by platform',
                'solution': 'Check content guidelines, verify technical specifications, remove copyrighted content'
            }
        ]
        
        platform_specific = {
            'instagram': [
                {
                    'problem': 'Video appears cropped',
                    'solution': 'Use 1:1 aspect ratio for feed posts, 9:16 for Stories and Reels'
                }
            ],
            'youtube': [
                {
                    'problem': 'Video not appearing in search',
                    'solution': 'Optimize title and description with relevant keywords, add proper tags'
                }
            ],
            'linkedin': [
                {
                    'problem': 'Low professional reach',
                    'solution': 'Post during business hours, use professional hashtags, engage with industry content'
                }
            ],
            'tiktok': [
                {
                    'problem': 'Video not going viral',
                    'solution': 'Use trending sounds, post at peak times, engage with trends, hook viewers quickly'
                }
            ]
        }
        
        return common_issues + platform_specific.get(platform, [])
    
    def get_workflow_templates(self, platform: str = None, workflow_type: str = None, 
                             category: str = None) -> List[Dict[str, Any]]:
        """
        Get available workflow templates with filtering
        """
        templates = []
        
        for template_key, template_data in self.workflow_templates.items():
            if workflow_type and workflow_type != template_key:
                continue
            
            template = {
                'id': template_key,
                'name': template_data['title'],
                'description': template_data['description'],
                'estimated_time': template_data['estimated_time'],
                'tools_needed': template_data['tools_needed'],
                'steps_count': len(template_data['steps']),
                'difficulty': self._assess_template_difficulty(template_key),
                'best_platforms': self._get_best_platforms_for_template(template_key),
                'category': self._get_template_category(template_key)
            }
            
            if category and category != template['category']:
                continue
            
            if platform and platform not in template['best_platforms']:
                continue
            
            templates.append(template)
        
        return templates
    
    def get_platform_requirements(self, platform: str) -> Dict[str, Any]:
        """
        Get comprehensive platform requirements
        """
        if platform not in self.platform_specs:
            return {}
        
        spec = self.platform_specs[platform]
        
        return {
            'technical_specs': spec,
            'content_guidelines': self._get_content_guidelines(platform),
            'best_practices': self._get_platform_best_practices(platform),
            'algorithm_tips': self._get_algorithm_tips(platform),
            'monetization_info': self._get_monetization_info(platform),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    
    def _assess_template_difficulty(self, template_key: str) -> str:
        """Assess difficulty level of template implementation"""
        difficulty_map = {
            'lifestyle_content': 'Easy',
            'testimonial': 'Easy',
            'avatar_presentation': 'Medium',
            'product_demo': 'Medium'
        }
        return difficulty_map.get(template_key, 'Medium')
    
    def _get_best_platforms_for_template(self, template_key: str) -> List[str]:
        """Get best platforms for each template type"""
        platform_map = {
            'product_demo': ['instagram', 'youtube', 'linkedin'],
            'avatar_presentation': ['linkedin', 'youtube'],
            'lifestyle_content': ['instagram', 'tiktok', 'facebook'],
            'testimonial': ['linkedin', 'facebook', 'youtube']
        }
        return platform_map.get(template_key, ['instagram', 'youtube'])
    
    def _get_template_category(self, template_key: str) -> str:
        """Get category for template"""
        category_map = {
            'product_demo': 'Business',
            'avatar_presentation': 'Professional',
            'lifestyle_content': 'Personal',
            'testimonial': 'Social Proof'
        }
        return category_map.get(template_key, 'General')
    
    def _get_content_guidelines(self, platform: str) -> List[str]:
        """Get platform content guidelines"""
        guidelines = {
            'instagram': [
                "No copyright infringement",
                "Authentic content preferred",
                "No misleading information",
                "Respect community standards"
            ],
            'youtube': [
                "Original content only",
                "No copyright strikes",
                "Family-friendly preferred",
                "Follow advertiser guidelines"
            ],
            'linkedin': [
                "Professional content focus",
                "No spam or irrelevant content",
                "Respectful professional discourse",
                "Value-driven posts preferred"
            ],
            'tiktok': [
                "Creative and entertaining content",
                "No dangerous challenges",
                "Respect community guidelines",
                "Original audio preferred"
            ]
        }
        return guidelines.get(platform, [])
    
    def _get_platform_best_practices(self, platform: str) -> List[str]:
        """Get platform-specific best practices"""
        practices = {
            'instagram': [
                "Use high-quality visuals",
                "Post consistently",
                "Engage with your audience",
                "Use relevant hashtags"
            ],
            'youtube': [
                "Create compelling thumbnails",
                "Optimize for search",
                "Maintain consistent branding",
                "Upload regularly"
            ],
            'linkedin': [
                "Share industry insights",
                "Network authentically",
                "Post during business hours",
                "Provide value to connections"
            ],
            'tiktok': [
                "Follow trends quickly",
                "Keep videos short and snappy",
                "Use trending sounds",
                "Post frequently"
            ]
        }
        return practices.get(platform, [])
    
    def _get_algorithm_tips(self, platform: str) -> List[str]:
        """Get algorithm optimization tips"""
        tips = {
            'instagram': [
                "High engagement in first hour is crucial",
                "Use relevant hashtags (10-30)",
                "Stories boost main feed visibility",
                "Consistent posting schedule helps"
            ],
            'youtube': [
                "Click-through rate on thumbnails matters",
                "Watch time is the most important factor",
                "Comments and likes boost ranking",
                "Upload during peak hours"
            ],
            'linkedin': [
                "Early engagement drives reach",
                "Professional hashtags work better",
                "Native video performs well",
                "Business hours posting optimal"
            ],
            'tiktok': [
                "Completion rate is crucial",
                "Trending hashtags and sounds help",
                "Quick hook in first 3 seconds",
                "User interaction drives reach"
            ]
        }
        return tips.get(platform, [])
    
    def _get_monetization_info(self, platform: str) -> Dict[str, Any]:
        """Get monetization information for platform"""
        monetization = {
            'instagram': {
                'requirements': '1,000+ followers, professional account',
                'methods': ['Sponsored posts', 'Instagram Shopping', 'Reels Play Bonus'],
                'revenue_share': '55% for Reels ads'
            },
            'youtube': {
                'requirements': '1,000 subscribers, 4,000 watch hours',
                'methods': ['Ad revenue', 'Channel memberships', 'Super Chat'],
                'revenue_share': '55% for ads, 70% for memberships'
            },
            'linkedin': {
                'requirements': 'No specific requirements',
                'methods': ['Lead generation', 'Sponsored content', 'LinkedIn Premium'],
                'revenue_share': 'Direct client payment'
            },
            'tiktok': {
                'requirements': '10,000+ followers, 100,000 video views',
                'methods': ['Creator Fund', 'Live gifts', 'Brand partnerships'],
                'revenue_share': 'Varies by program'
            }
        }
        return monetization.get(platform, {})