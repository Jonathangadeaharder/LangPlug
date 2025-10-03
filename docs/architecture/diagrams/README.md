# LangPlug Architecture Diagrams

This directory contains comprehensive PlantUML architecture diagrams for the LangPlug language learning platform.

## Diagram Overview

### 1. System Context Diagram (`system-context.puml`)

**C4 Model Level 1** - Shows the big picture of the LangPlug system and its interactions with users and external systems.

- **Actors**: Language Learner, Administrator
- **External Systems**: Whisper AI, NLLB Translation, SpaCy NLP, Video Storage, Database
- **Purpose**: Understand the system boundaries and external dependencies

### 2. Container Diagram (`container-diagram.puml`)

**C4 Model Level 2** - Shows the high-level technology choices and how containers communicate.

- **Containers**: Frontend (React), Backend API (FastAPI), WebSocket Server, Database, AI Services
- **Technologies**: React + TypeScript, FastAPI + Python, PostgreSQL, Whisper, NLLB, SpaCy
- **Purpose**: Understand the major building blocks and technology stack

### 3. Backend Component Diagram (`backend-components.puml`)

**C4 Model Level 3** - Detailed view of the FastAPI backend architecture.

- **Layers**: API Routes, Service Layer, Repository Layer, Core Infrastructure
- **Components**: Auth, Video, Vocabulary, Processing, Transcription, Translation services
- **Purpose**: Understand backend internal structure and layered architecture

### 4. Frontend Component Diagram (`frontend-components.puml`)

**C4 Model Level 3** - Detailed view of the React frontend architecture.

- **Components**: Pages, UI Components, API Client, State Management
- **Key Features**: ChunkedLearningFlow, VideoSelection, VocabularyGame, SubtitleViewer
- **Purpose**: Understand frontend structure and component relationships

### 5. Authentication Sequence Diagram (`sequence-authentication.puml`)

Shows the complete user authentication flow with JWT and cookies.

- **Flow**: Login form → API authentication → JWT generation → Cookie setting → Session establishment
- **Security**: Password hashing, HttpOnly cookies, token validation
- **Purpose**: Understand authentication and session management

### 6. Video Processing Sequence Diagram (`sequence-video-processing.puml`)

Shows the complete video processing pipeline with real-time progress updates.

- **Phases**:
  1. Transcription (Whisper AI) - 0-40%
  2. Translation (NLLB AI) - 40-70%
  3. Vocabulary Extraction (SpaCy) - 70-90%
  4. Finalization - 90-100%
- **Real-time**: WebSocket progress updates throughout processing
- **Purpose**: Understand the AI-powered video processing workflow

### 7. Entity-Relationship Diagram (`entity-relationship.puml`)

Shows the database schema and relationships between entities.

- **Core Entities**: User, Video, Vocabulary, UserVocabulary, ProcessingTask, LearningSession, VideoChunk
- **Relationships**: User learning progress, video processing, spaced repetition system
- **Purpose**: Understand data model and database structure

### 8. Deployment Diagram (`deployment-diagram.puml`)

Shows the physical deployment architecture and infrastructure.

- **Nodes**: User Browser, Application Server, AI Model Server (GPU), Database Server, Storage Server
- **Environments**: Development (WSL2/macOS) and Production configurations
- **Purpose**: Understand deployment topology and infrastructure requirements

## How to Use These Diagrams

### Viewing Diagrams

#### Option 1: PlantUML Online Server

1. Copy the `.puml` file content
2. Visit [PlantUML Online](http://www.plantuml.com/plantuml/uml/)
3. Paste the content and view the diagram

#### Option 2: VS Code Extension

1. Install the "PlantUML" extension in VS Code
2. Open any `.puml` file
3. Press `Alt+D` (or `Cmd+D` on macOS) to preview

#### Option 3: Command Line (with PlantUML installed)

**Prerequisites**: Requires Java and Graphviz

```bash
# Install Graphviz (required for PlantUML rendering)
# On Ubuntu/Debian:
sudo apt-get install graphviz

# On macOS:
brew install graphviz

# Install PlantUML
# On Ubuntu/Debian:
sudo apt-get install plantuml

# On macOS:
brew install plantuml

# Or use PlantUML jar directly (Java required):
wget https://sourceforge.net/projects/plantuml/files/plantuml.jar/download -O plantuml.jar
java -jar plantuml.jar *.puml

# Generate PNG images
plantuml *.puml

# Generate SVG (scalable)
plantuml -tsvg *.puml
```

### Generating Images

To generate PNG/SVG images from all diagrams:

```bash
# Navigate to diagrams directory
cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/docs/architecture/diagrams

# Generate all PNGs
plantuml *.puml

# Generate all SVGs (recommended for documentation)
plantuml -tsvg *.puml
```

## Diagram Conventions

### C4 Model Diagrams

- **System Context**: Shows the big picture - system and users/external systems
- **Container**: Shows high-level technology choices - applications, databases, file systems
- **Component**: Shows components within a container - modules, services, repositories

### Color Coding

- **Blue tones**: User interface and frontend components
- **Purple tones**: Backend services and APIs
- **Green tones**: Data storage and persistence
- **Orange tones**: External systems and AI services
- **Gray tones**: Infrastructure and deployment nodes

### Relationship Types

- **Solid arrows**: Synchronous communication (HTTP, function calls)
- **Dashed arrows**: Asynchronous communication (WebSocket, message queues)
- **Bold arrows**: Primary data flow
- **Thin arrows**: Secondary/auxiliary flow

## Architecture Principles Reflected in Diagrams

1. **Layered Architecture**: Clear separation between API, Service, and Repository layers
2. **Microservices Ready**: Loosely coupled services that can be independently deployed
3. **AI Integration**: Dedicated AI services with clear interfaces
4. **Real-time Communication**: WebSocket for progress updates and live notifications
5. **Scalability**: Horizontal scaling of API servers, GPU-based AI services
6. **Security**: JWT authentication, secure communication, proper data isolation

## Updating Diagrams

When making architectural changes:

1. **Update the relevant `.puml` file** with new components or relationships
2. **Regenerate images** using PlantUML
3. **Update this README** if adding new diagrams or changing conventions
4. **Commit both `.puml` source and generated images** to version control

## Tools and Resources

- **PlantUML Official**: https://plantuml.com/
- **C4 Model**: https://c4model.com/
- **PlantUML C4**: https://github.com/plantuml-stdlib/C4-PlantUML
- **PlantUML Themes**: https://the-lum.github.io/puml-themes-gallery/

## Diagram Maintenance

These diagrams should be updated when:

- ✅ Adding new major features or components
- ✅ Changing database schema
- ✅ Modifying API architecture or service boundaries
- ✅ Adding new external integrations
- ✅ Changing deployment infrastructure
- ✅ Updating authentication/security mechanisms

Keep diagrams in sync with code to maintain their value as documentation.

---

## New Diagrams (2025-10-03)

The following comprehensive diagrams have been added:

1. **`01-system-context.puml`** - C4 System Context (replaces system-context.puml)
2. **`02-container-diagram.puml`** - C4 Container Diagram (replaces container-diagram.puml)
3. **`03-component-diagram.puml`** - Backend Components (replaces backend-components.puml)
4. **`04-database-schema.puml`** - Database ER Diagram (replaces entity-relationship.puml)
5. **`05-authentication-sequence.puml`** - Auth Flow (replaces sequence-authentication.puml)
6. **`06-video-processing-sequence.puml`** - Processing Pipeline (replaces sequence-video-processing.puml)
7. **`07-vocabulary-learning-flow.puml`** - Learning Journey (activity diagram)
8. **`08-deployment-architecture.puml`** - Production Deployment (replaces deployment-diagram.puml)
9. **`09-layered-architecture.puml`** - Layered Architecture Pattern (new)

All diagrams follow consistent naming (numbered) and use latest C4-PlantUML and BluePrint theme.

---

**Last Updated**: 2025-10-03
**Maintained By**: LangPlug Development Team
