<h1 align="center">BOULDERING CYPRUS - Your Ultimate Guide to Bouldering in Cyprus</h1>

"Bouldering Cyprus" is a Django-based e-commerce web application designed to promote and support the bouldering community in Cyprus. The platform offers an online shop selling the comprehensive guidebook (physical book) for bouldering spots across the island, crashpad rentals. This application aims to make bouldering in Cyprus more accessible to both locals and tourists by providing essential information, equipment, and services. It is designed to be scalable and has the potential to easily host other related climbing products as the offering expands.

<div style="text-align:center">
<a href="https://bouldering-cyprus-53e1273cde1e.herokuapp.com/">ACCESS THE APPLICATION</a></div>

# App Overview

## App Purpose / User Goals
The Bouldering Cyprus app aims to serve as a central hub for the bouldering community in Cyprus by offering:

- **Guidebook Sales:** The main purpose is to market and sell the Bouldering Cyprus Guidebook, a physical book containing detailed information about bouldering spots across Cyprus, including maps, route descriptions, and difficulty ratings.

- **Equipment Rental:** Offering crashpad rentals to visitors who don't want to travel with their own equipment.

- **E-commerce Platform:** Capacity to sell guidebooks and other bouldering-related products as the offering expands.

- **Community Building:** Creating a platform for the local bouldering community to connect and share information via the social media pages and the newsletter.

- **Newsletter Subscription:** Keeping users updated with the latest bouldering news, spot discoveries, and events in Cyprus.

## Key Features

- **Responsive Design:** Fully responsive website that works seamlessly across desktop, tablet, and mobile devices.

- **User Authentication:** Secure user registration and authentication system using Django Allauth.

- **Product Management:** Comprehensive product catalog with detailed descriptions, images, and pricing.

- **Shopping Cart:** Intuitive shopping cart functionality allowing users to add, update, and remove items.

- **Secure Checkout:** Integration with Stripe for secure payment processing.

- **Crashpad Rental System:** Dedicated rental system for crashpads with date selection and availability checking.

- **Order Management:** Complete order tracking and management system for both users and administrators.

- **Newsletter Subscription:** Email newsletter subscription system to keep users informed about updates.

- **Admin Dashboard:** Comprehensive admin interface for managing products, orders, rentals, and users.

- **Error Monitoring:** Integration with Sentry for real-time error tracking and monitoring.

# App Design & Planning

## User Stories
### Must have

| Title | User Story | Acceptance Criteria |
| ----------- | ----------- | ----------- |
User Registration and Authentication | As a user, I can register for an account and log in so that I can access personalized features | <ul><li>User can register with email verification</li><li>User can log in and log out</li><li>User can reset password</li></ul> |
Browse Products | As a user, I can view all available products so that I can select items to purchase | <ul><li>Products are displayed with images, titles, and prices</li><li>Products can be sorted and filtered</li><li>Product details are accessible</li></ul> |
Shopping Cart | As a user, I can add products to a cart so that I can purchase multiple items at once | <ul><li>Items can be added to cart</li><li>Cart quantities can be updated</li><li>Items can be removed from cart</li></ul> |
Checkout Process | As a user, I can securely checkout and pay for my items so that I can complete my purchase | <ul><li>Secure payment processing with Stripe</li><li>Order confirmation is displayed</li><li>Confirmation email is sent</li></ul> |
Crashpad Rental | As a user, I can rent crashpads for specific dates so that I can go bouldering without bringing my own equipment | <ul><li>Available crashpads can be viewed</li><li>Rental dates can be selected</li><li>Rental can be added to cart</li></ul> |
View Order History | As a user, I can view my order history so that I can keep track of my purchases | <ul><li>List of past orders is displayed</li><li>Order details can be viewed</li><li>Order status is shown</li></ul> |
Newsletter Subscription | As a user, I can subscribe to the newsletter so that I can stay updated with bouldering news in Cyprus | <ul><li>Newsletter subscription form is available</li><li>Confirmation email is sent</li><li>Unsubscribe option is provided</li></ul> |

### Should have
| Title | User Story | Acceptance Criteria |
| ----------- | ----------- | ----------- |
Product Reviews | As a user, I can leave reviews on products so that I can share my experience with others | <ul><li>Reviews can be submitted with ratings</li><li>Reviews are displayed on product pages</li><li>Average rating is calculated</li></ul> |
User Profile | As a user, I can manage my profile information so that I can update my details and preferences | <ul><li>User can edit personal information</li><li>User can view order history</li><li>User can manage payment methods</li></ul> |
Admin Product Management | As an admin, I can add, edit, and delete products so that I can manage the store inventory | <ul><li>Products can be added through admin interface</li><li>Product details can be edited</li><li>Products can be removed</li></ul> |
Admin Order Management | As an admin, I can view and manage orders so that I can process customer purchases | <ul><li>Orders can be viewed in admin interface</li><li>Order status can be updated</li><li>Order details can be accessed</li></ul> |

### Could have
| Title | User Story | Acceptance Criteria |
| ----------- | ----------- | ----------- |
Bouldering Spot Information | As a user, I can view information about bouldering spots in Cyprus so that I can plan my climbing trips | <ul><li>Spot locations are displayed on a map</li><li>Spot details include difficulty levels and access information</li><li>Photos of spots are available</li></ul> |
Wishlist | As a user, I can save products to a wishlist so that I can purchase them later | <ul><li>Products can be added to wishlist</li><li>Wishlist items can be viewed</li><li>Items can be moved from wishlist to cart</li></ul> |
Social Media Integration | As a user, I can share products on social media so that I can recommend them to friends | <ul><li>Social sharing buttons are available</li><li>Shared links include product images and descriptions</li><li>Sharing analytics are tracked</li></ul> |

### Won't have
| Title | User Story | Acceptance Criteria |
| ----------- | ----------- | ----------- |
Live Chat Support | As a user, I can chat with customer support in real-time so that I can get immediate assistance | <ul><li>Chat widget is available on all pages</li><li>Support agents can respond in real-time</li><li>Chat history is saved</li></ul> |
Mobile App | As a user, I can use a dedicated mobile app so that I can access the platform more conveniently on my phone | <ul><li>App is available on iOS and Android</li><li>App has same functionality as website</li><li>App sends push notifications</li></ul> |
Loyalty Program | As a user, I can earn points for purchases so that I can get discounts on future orders | <ul><li>Points are awarded for purchases</li><li>Points can be redeemed for discounts</li><li>Point balance is displayed in user profile</li></ul> |

## Typography & Colours
### Fonts
The application uses a combination of modern, readable fonts to enhance user experience:

- **Primary Font:** The main content uses a clean, sans-serif font for optimal readability across devices.
- **Accent Font:** "Roboto Condensed" is used for headings and important text elements to create visual hierarchy.

### Colour palette
The color palette is inspired by the natural landscapes of Cyprus and bouldering environments:

- **Primary Colors:** Earth tones and rock-inspired colors that reflect the natural bouldering environment.
- **Accent Colors:** Vibrant highlights to draw attention to important elements like calls-to-action.
- **Background:** Light, neutral backgrounds to ensure content readability and reduce eye strain.

The application uses Bootstrap 5 background colors for consistency, with bg-primary and bg-light being the dominant colors across the app.

## Database
### Design
The database design focuses on efficiently managing products, orders, rentals, and user data. The main models include:

- **User Model:** Extended Django user model with additional profile information.
- **Product Model:** Stores information about guidebooks and other products available for purchase.
- **Order Model:** Tracks customer orders, payment status, and delivery information.
- **OrderItem Model:** Links products to orders with quantity and price information.
- **Rental Model:** Manages crashpad rentals with date ranges and availability.
- **Newsletter Model:** Stores subscriber information for the newsletter system.

### Implementation
The database is implemented using PostgreSQL in production and SQLite for development/testing. Django ORM is used for database operations, providing a clean abstraction layer for data management.

## Technologies & Tools Stack

This project utilizes a robust stack of technologies and tools to deliver a seamless experience in development and functionality:

### Programming Languages
- **[Python](https://www.python.org/)**: The core programming language used for backend logic and full-stack application development.
- **[JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)**: For dynamic front-end functionality and interactive features.
- **[HTML5](https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/HTML5)**: Structuring web pages with semantic markup.
- **[CSS3](https://developer.mozilla.org/en-US/docs/Web/CSS)**: For styling the front-end and ensuring a responsive design.

### Frameworks
- **[Django](https://www.djangoproject.com/)**: A high-level Python web framework that enables rapid development and clean, pragmatic design.
- **[Bootstrap 5](https://getbootstrap.com/)**: For responsive design and pre-styled components.

### Libraries & Packages
- **[Django Allauth](https://django-allauth.readthedocs.io/)**: For user authentication, registration, and account management.
- **[Django Crispy Forms](https://django-crispy-forms.readthedocs.io/)**: For rendering beautiful and customizable forms.
- **[Django Summernote](https://github.com/summernote/django-summernote)**: For rich text editing in the admin interface.
- **[Django Storages](https://django-storages.readthedocs.io/)**: For handling file storage with AWS S3.
- **[Django REST Framework](https://www.django-rest-framework.org/)**: For building APIs.
- **[Stripe](https://stripe.com/)**: For secure payment processing.
- **[AWS S3](https://aws.amazon.com/s3/)**: For storing static and media files.
- **[Sentry](https://sentry.io/)**: For error tracking and monitoring.

### Development Tools
- **[Git](https://git-scm.com/)**: For version control.
- **[GitHub](https://github.com/)**: For source code management.
- **[VS Code](https://code.visualstudio.com/)**: As the primary code editor.
- **[Chrome DevTools](https://developers.google.com/web/tools/chrome-devtools)**: For debugging and testing.

### Deployment & Hosting
- **[Heroku](https://www.heroku.com/)**: For application hosting.
- **[AWS CloudFront](https://aws.amazon.com/cloudfront/)**: For content delivery network services.
- **[PostgreSQL](https://www.postgresql.org/)**: As the production database.

# Testing

## Automated Testing
The application includes a comprehensive suite of automated tests to ensure functionality and reliability:

- **Unit Tests:** Testing individual components and functions in isolation.
- **Integration Tests:** Testing the interaction between different parts of the application.
- **View Tests:** Ensuring views return the correct responses and templates.
- **Form Tests:** Validating form functionality and validation.
- **Model Tests:** Testing model methods and relationships.

## Manual Testing
Manual testing was conducted to verify user experience and functionality:

- **Responsive Design:** Tested across multiple devices and screen sizes.
- **Browser Compatibility:** Tested on Chrome, Firefox, Safari, and Edge.
- **User Flows:** Walked through common user journeys from browsing to checkout.
- **Payment Processing:** Verified Stripe integration and payment flows.
- **Error Handling:** Tested application behavior with invalid inputs and edge cases.

## Code Validation
All code was validated using industry-standard tools:

- **HTML:** Validated using the W3C HTML Validator.
- **CSS:** Validated using the W3C CSS Validator.
- **JavaScript:** Validated using JSHint.
- **Python:** Validated using PEP8 standards and Flake8.

## Lighthouse Audit
Performance, accessibility, best practices, and SEO were tested using Lighthouse:

- **Performance:** Optimized for fast loading times.
- **Accessibility:** Ensured the application is accessible to all users.
- **Best Practices:** Followed web development best practices.
- **SEO:** Optimized for search engine visibility.

## Error Monitoring with Sentry
The application uses Sentry for comprehensive error monitoring and tracking:

- **Real-Time Error Tracking:** Captures and displays errors as they occur.
- **Contextual Information:** Includes stack traces and request context in error reports.
- **JavaScript Error Tracking:** Logs frontend issues for seamless debugging.
- **Alerts and Notifications:** Sends alerts for critical issues.

# Deployment

## Deployment to Heroku
The application is deployed on Heroku with the following configuration:

1. **Create a Heroku App:** Set up a new app on Heroku.
2. **Configure Environment Variables:** Set up all necessary environment variables in Heroku settings.
3. **Database Setup:** Provision a PostgreSQL database.
4. **Static Files:** Configure AWS S3 for static and media file storage.
5. **Deploy:** Connect GitHub repository and enable automatic deployments.

## Environment Variables
The following environment variables are required:

- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL database URL
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_STORAGE_BUCKET_NAME`: S3 bucket name
- `STRIPE_PUBLIC_KEY`: Stripe public key
- `STRIPE_SECRET_KEY`: Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret
- `EMAIL_HOST_KEY`: SendGrid API key
- `DEFAULT_EMAIL`: Default sender email

## Local Development
To run the project locally:

1. Clone the repository: `git clone https://github.com/yourusername/bouldering-cyprus.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in an `env.py` file
4. Run migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run the server: `python manage.py runserver`

# Credits

## Technical
| Source | Use | Notes |
| ------ | --- | ----- |
| [Django Documentation](https://docs.djangoproject.com/) | Framework reference | Extensive research on Django concepts |
| [Stripe Documentation](https://stripe.com/docs) | Payment integration | Implementation of secure checkout |
| [Bootstrap Documentation](https://getbootstrap.com/docs/) | Frontend framework | Responsive design implementation |
| [AWS S3 Documentation](https://docs.aws.amazon.com/s3/) | File storage | Static and media file management |
| [Sentry Documentation](https://docs.sentry.io/) | Error monitoring | Implementation of error tracking |

## Content
| Source | Use | Notes |
| ------ | --- | ----- |
| [FontAwesome](https://fontawesome.com/) | Icons | Used throughout the site |
| Original Content | Product descriptions | Written specifically for this application |
| Original Content | Bouldering information | Based on local knowledge and research |

## Media
| Source | Use | Notes |
| ------ | --- | ----- |
| Original Photography | Product images | Taken specifically for this application |
| Original Photography | Bouldering spot images | Captured at various locations in Cyprus |

# Acknowledgements
* I would like to thank my Code Institute mentor for their guidance and support throughout this project.
* Special thanks to the bouldering community in Cyprus for their input and feedback during the development process.
* I would also like to acknowledge the Code Institute for providing the knowledge and resources needed to create this application.
